import os
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Employer, Candidate, Job, Application, Notification, validate_resume_file

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class EmployerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Employer
        fields = ['id', 'user', 'company_name', 'description', 'website']

class CandidateSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Candidate
        fields = ['id', 'user', 'full_name', 'phone', 'skills', 'resume']

class EmployerRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6)
    company_name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username already exists.')
        return value

    def create(self, validated_data):
        username = validated_data['username']
        email = validated_data.get('email', '')
        password = validated_data['password']
        company_name = validated_data['company_name']
        description = validated_data.get('description', '')
        website = validated_data.get('website', '')

        user = User.objects.create_user(username=username, email=email, password=password)
        employer = Employer.objects.create(
            user=user,
            company_name=company_name,
            description=description,
            website=website
        )
        return employer

class CandidateRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6)
    full_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    skills = serializers.CharField(required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username already exists.')
        return value

    def create(self, validated_data):
        username = validated_data['username']
        email = validated_data.get('email', '')
        password = validated_data['password']
        full_name = validated_data['full_name']
        phone = validated_data.get('phone', '')
        skills = validated_data.get('skills', '')

        user = User.objects.create_user(username=username, email=email, password=password)
        candidate = Candidate.objects.create(
            user=user,
            full_name=full_name,
            phone=phone,
            skills=skills
        )
        return candidate

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs.get('username'), password=attrs.get('password'))
        if not user:
            raise serializers.ValidationError('Invalid username or password.')
        attrs['user'] = user
        return attrs

class JobSerializer(serializers.ModelSerializer):
    employer = EmployerSerializer(read_only=True)

    class Meta:
        model = Job
        fields = [
            'id',
            'employer',
            'title',
            'description',
            'location',
            'job_type',
            'salary',
            'skills_required',
            'created_at',
            'is_active',
        ]

class ResumeUploadSerializer(serializers.ModelSerializer):
    resume = serializers.FileField(validators=[validate_resume_file])

    class Meta:
        model = Candidate
        fields = ['resume']

class ApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['cover_letter']

class ApplicationSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    candidate = CandidateSerializer(read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'job', 'candidate', 'cover_letter', 'status', 'applied_at']

class ApplicationStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['status']

    def validate_status(self, value):
        valid_statuses = [choice[0] for choice in Application.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return value

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'message', 'is_read', 'created_at']
