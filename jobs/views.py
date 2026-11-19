from django.db.models import Q
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.authtoken.models import Token
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404

from .models import Employer, Candidate, Job, Application, Notification
from .permissions import IsEmployer, IsCandidate
from .serializers import (
    EmployerRegistrationSerializer,
    CandidateRegistrationSerializer,
    EmployerSerializer,
    CandidateSerializer,
    LoginSerializer,
    JobSerializer,
    ResumeUploadSerializer,
    ApplicationCreateSerializer,
    ApplicationSerializer,
    ApplicationStatusUpdateSerializer,
    NotificationSerializer,
)

class EmployerRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmployerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            employer = serializer.save()
            token, _ = Token.objects.get_or_create(user=employer.user)
            return Response({
                'token': token.key,
                'user_id': employer.user.id,
                'username': employer.user.username,
                'role': 'employer',
                'employer': EmployerSerializer(employer).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CandidateRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CandidateRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            candidate = serializer.save()
            token, _ = Token.objects.get_or_create(user=candidate.user)
            return Response({
                'token': token.key,
                'user_id': candidate.user.id,
                'username': candidate.user.username,
                'role': 'candidate',
                'candidate': CandidateSerializer(candidate).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, _ = Token.objects.get_or_create(user=user)
            role = 'admin' if user.is_staff or user.is_superuser else (
                'employer' if hasattr(user, 'employer_profile') else (
                    'candidate' if hasattr(user, 'candidate_profile') else 'user'
                )
            )
            return Response({
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
                'role': role
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class JobListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsEmployer()]
        return [AllowAny()]

    def get(self, request):
        queryset = Job.objects.filter(is_active=True).order_by('-created_at')

        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(skills_required__icontains=search)
            )

        location = request.query_params.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location)

        job_type = request.query_params.get('job_type')
        if job_type:
            queryset = queryset.filter(job_type__iexact=job_type)

        min_salary = request.query_params.get('min_salary')
        if min_salary:
            try:
                queryset = queryset.filter(salary__gte=float(min_salary))
            except ValueError:
                pass

        serializer = JobSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = JobSerializer(data=request.data)
        if serializer.is_valid():
            job = serializer.save(employer=request.user.employer_profile)
            return Response(JobSerializer(job).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class JobDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        job = get_object_or_404(Job, pk=pk)
        serializer = JobSerializer(job)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ResumeUploadView(APIView):
    permission_classes = [IsAuthenticated, IsCandidate]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        candidate = request.user.candidate_profile
        serializer = ResumeUploadSerializer(candidate, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(CandidateSerializer(candidate).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class JobApplyView(APIView):
    permission_classes = [IsAuthenticated, IsCandidate]

    def post(self, request, pk):
        job = get_object_or_404(Job, pk=pk)
        if not job.is_active:
            return Response({'error': 'This job is no longer active.'}, status=status.HTTP_400_BAD_REQUEST)

        candidate = request.user.candidate_profile
        if Application.objects.filter(job=job, candidate=candidate).exists():
            return Response({'error': 'You have already applied for this job.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ApplicationCreateSerializer(data=request.data)
        if serializer.is_valid():
            application = serializer.save(job=job, candidate=candidate)
            Notification.objects.create(
                user=job.employer.user,
                message=f"{candidate.full_name} applied for your job: {job.title}"
            )
            return Response(ApplicationSerializer(application).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MyApplicationsView(APIView):
    permission_classes = [IsAuthenticated, IsCandidate]

    def get(self, request):
        candidate = request.user.candidate_profile
        applications = candidate.applications.all().order_by('-applied_at')
        serializer = ApplicationSerializer(applications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class JobApplicationsView(APIView):
    permission_classes = [IsAuthenticated, IsEmployer]

    def get(self, request, pk):
        job = get_object_or_404(Job, pk=pk)
        if job.employer != request.user.employer_profile:
            return Response({'error': 'You can only view applications for your own jobs.'}, status=status.HTTP_403_FORBIDDEN)

        applications = job.applications.all().order_by('-applied_at')
        serializer = ApplicationSerializer(applications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ApplicationStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsEmployer]

    def patch(self, request, pk):
        application = get_object_or_404(Application, pk=pk)
        if application.job.employer != request.user.employer_profile:
            return Response({'error': 'You can only update status for applications to your own jobs.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ApplicationStatusUpdateSerializer(application, data=request.data, partial=True)
        if serializer.is_valid():
            old_status = application.status
            updated_application = serializer.save()
            new_status = updated_application.status
            if old_status != new_status:
                Notification.objects.create(
                    user=application.candidate.user,
                    message=f"Your application status for {application.job.title} has been updated to {new_status}."
                )
            return Response(ApplicationSerializer(updated_application).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = request.user.notifications.all().order_by('-created_at')
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AdminStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        total_jobs = Job.objects.count()
        total_applications = Application.objects.count()
        applications_per_status = {
            choice[0]: Application.objects.filter(status=choice[0]).count()
            for choice in Application.STATUS_CHOICES
        }
        return Response({
            'total_jobs': total_jobs,
            'total_applications': total_applications,
            'applications_per_status': applications_per_status
        }, status=status.HTTP_200_OK)
