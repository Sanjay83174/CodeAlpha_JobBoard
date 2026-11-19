from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from .models import Employer, Candidate, Job, Application, Notification

class JobBoardTests(APITestCase):
    def setUp(self):
        self.employer_user = User.objects.create_user(
            username='techcorp',
            email='hr@techcorp.com',
            password='Password123!'
        )
        self.employer = Employer.objects.create(
            user=self.employer_user,
            company_name='TechCorp Inc',
            description='A tech company',
            website='https://techcorp.com'
        )
        self.employer_token, _ = Token.objects.get_or_create(user=self.employer_user)

        self.candidate_user = User.objects.create_user(
            username='johndoe',
            email='john@example.com',
            password='Password123!'
        )
        self.candidate = Candidate.objects.create(
            user=self.candidate_user,
            full_name='John Doe',
            phone='1234567890',
            skills='Python, Django, React'
        )
        self.candidate_token, _ = Token.objects.get_or_create(user=self.candidate_user)

        self.other_employer_user = User.objects.create_user(
            username='othercorp',
            email='hr@othercorp.com',
            password='Password123!'
        )
        self.other_employer = Employer.objects.create(
            user=self.other_employer_user,
            company_name='OtherCorp',
            description='Another tech company',
            website='https://othercorp.com'
        )
        self.other_employer_token, _ = Token.objects.get_or_create(user=self.other_employer_user)

        self.admin_user = User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='AdminPassword123!'
        )
        self.admin_token, _ = Token.objects.get_or_create(user=self.admin_user)

        self.job = Job.objects.create(
            employer=self.employer,
            title='Backend Engineer',
            description='Build REST APIs',
            location='Remote',
            job_type='full-time',
            salary=90000.00,
            skills_required='Python, Django',
            is_active=True
        )

    def test_employer_registration(self):
        url = reverse('register-employer')
        data = {
            'username': 'innovate',
            'email': 'contact@innovate.com',
            'password': 'SecurePassword123',
            'company_name': 'Innovate Ltd',
            'description': 'AI startup',
            'website': 'https://innovate.ai'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['role'], 'employer')
        self.assertEqual(Employer.objects.filter(company_name='Innovate Ltd').count(), 1)

    def test_candidate_registration(self):
        url = reverse('register-candidate')
        data = {
            'username': 'janesmith',
            'email': 'jane@example.com',
            'password': 'SecurePassword123',
            'full_name': 'Jane Smith',
            'phone': '9876543210',
            'skills': 'JavaScript, Node.js'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['role'], 'candidate')
        self.assertEqual(Candidate.objects.filter(full_name='Jane Smith').count(), 1)

    def test_login(self):
        url = reverse('login')
        data = {'username': 'techcorp', 'password': 'Password123!'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'employer')
        self.assertEqual(response.data['token'], self.employer_token.key)

        bad_data = {'username': 'techcorp', 'password': 'WrongPassword'}
        response = self.client.post(url, bad_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_job_by_employer(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.employer_token.key)
        url = reverse('job-list-create')
        data = {
            'title': 'Frontend Developer',
            'description': 'React and TypeScript',
            'location': 'New York',
            'job_type': 'contract',
            'salary': 75000.00,
            'skills_required': 'React, CSS, HTML'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Frontend Developer')
        self.assertEqual(response.data['employer']['company_name'], 'TechCorp Inc')

    def test_post_job_by_candidate_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.candidate_token.key)
        url = reverse('job-list-create')
        data = {
            'title': 'Frontend Developer',
            'description': 'React and TypeScript',
            'location': 'New York',
            'job_type': 'contract',
            'salary': 75000.00,
            'skills_required': 'React'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_job_listing_and_filtering(self):
        Job.objects.create(
            employer=self.employer,
            title='DevOps Specialist',
            description='Kubernetes AWS',
            location='London',
            job_type='part-time',
            salary=50000.00,
            skills_required='AWS, Docker',
            is_active=True
        )

        url = reverse('job-list-create')
        res_all = self.client.get(url)
        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_all.data), 2)

        res_search = self.client.get(url + '?search=DevOps')
        self.assertEqual(len(res_search.data), 1)
        self.assertEqual(res_search.data[0]['title'], 'DevOps Specialist')

        res_loc = self.client.get(url + '?location=Remote')
        self.assertEqual(len(res_loc.data), 1)
        self.assertEqual(res_loc.data[0]['title'], 'Backend Engineer')

        res_type = self.client.get(url + '?job_type=part-time')
        self.assertEqual(len(res_type.data), 1)
        self.assertEqual(res_type.data[0]['title'], 'DevOps Specialist')

        res_salary = self.client.get(url + '?min_salary=80000')
        self.assertEqual(len(res_salary.data), 1)
        self.assertEqual(res_salary.data[0]['title'], 'Backend Engineer')

    def test_job_details(self):
        url = reverse('job-detail', kwargs={'pk': self.job.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Backend Engineer')

    def test_resume_upload(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.candidate_token.key)
        url = reverse('resume-upload')

        valid_pdf = SimpleUploadedFile("resume.pdf", b"%PDF-1.4 dummy pdf content", content_type="application/pdf")
        response = self.client.post(url, {'resume': valid_pdf}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.candidate.refresh_from_db()
        self.assertTrue(self.candidate.resume.name.endswith('.pdf'))

        invalid_file = SimpleUploadedFile("script.py", b"print('hello')", content_type="text/x-python")
        response_invalid = self.client.post(url, {'resume': invalid_file}, format='multipart')
        self.assertEqual(response_invalid.status_code, status.HTTP_400_BAD_REQUEST)

        oversized_content = b"x" * (5 * 1024 * 1024 + 10)
        oversized_file = SimpleUploadedFile("huge.pdf", oversized_content, content_type="application/pdf")
        response_oversized = self.client.post(url, {'resume': oversized_file}, format='multipart')
        self.assertEqual(response_oversized.status_code, status.HTTP_400_BAD_REQUEST)

    def test_job_application_flow(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.candidate_token.key)
        apply_url = reverse('job-apply', kwargs={'pk': self.job.id})
        apply_data = {'cover_letter': 'I am passionate about Django.'}
        response = self.client.post(apply_url, apply_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'applied')

        employer_notifications = Notification.objects.filter(user=self.employer_user)
        self.assertEqual(employer_notifications.count(), 1)
        self.assertIn('John Doe applied for your job', employer_notifications.first().message)

        dup_response = self.client.post(apply_url, apply_data, format='json')
        self.assertEqual(dup_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already applied', dup_response.data['error'])

        my_apps_url = reverse('my-applications')
        my_apps_response = self.client.get(my_apps_url)
        self.assertEqual(my_apps_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(my_apps_response.data), 1)

    def test_employer_view_applicants(self):
        application = Application.objects.create(
            job=self.job,
            candidate=self.candidate,
            cover_letter='Excited to apply!'
        )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.employer_token.key)
        url = reverse('job-applications', kwargs={'pk': self.job.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['candidate']['full_name'], 'John Doe')

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.other_employer_token.key)
        forbidden_response = self.client.get(url)
        self.assertEqual(forbidden_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_application_status_update(self):
        application = Application.objects.create(
            job=self.job,
            candidate=self.candidate,
            cover_letter='Interested'
        )

        status_url = reverse('application-status-update', kwargs={'pk': application.id})

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.candidate_token.key)
        cand_resp = self.client.patch(status_url, {'status': 'shortlisted'}, format='json')
        self.assertEqual(cand_resp.status_code, status.HTTP_403_FORBIDDEN)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.other_employer_token.key)
        other_resp = self.client.patch(status_url, {'status': 'shortlisted'}, format='json')
        self.assertEqual(other_resp.status_code, status.HTTP_403_FORBIDDEN)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.employer_token.key)
        emp_resp = self.client.patch(status_url, {'status': 'shortlisted'}, format='json')
        self.assertEqual(emp_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(emp_resp.data['status'], 'shortlisted')

        candidate_notifications = Notification.objects.filter(user=self.candidate_user)
        self.assertEqual(candidate_notifications.count(), 1)
        self.assertIn('shortlisted', candidate_notifications.first().message)

        notif_url = reverse('notifications')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.candidate_token.key)
        notif_resp = self.client.get(notif_url)
        self.assertEqual(notif_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(notif_resp.data), 1)

    def test_admin_stats(self):
        Application.objects.create(
            job=self.job,
            candidate=self.candidate,
            cover_letter='Cover letter',
            status='applied'
        )

        url = reverse('admin-stats')

        unauth_resp = self.client.get(url)
        self.assertEqual(unauth_resp.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.candidate_token.key)
        cand_resp = self.client.get(url)
        self.assertEqual(cand_resp.status_code, status.HTTP_403_FORBIDDEN)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.employer_token.key)
        emp_resp = self.client.get(url)
        self.assertEqual(emp_resp.status_code, status.HTTP_403_FORBIDDEN)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        admin_resp = self.client.get(url)
        self.assertEqual(admin_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(admin_resp.data['total_jobs'], 1)
        self.assertEqual(admin_resp.data['total_applications'], 1)
        self.assertIn('applications_per_status', admin_resp.data)
        self.assertEqual(admin_resp.data['applications_per_status']['applied'], 1)
        self.assertEqual(admin_resp.data['applications_per_status']['hired'], 0)
