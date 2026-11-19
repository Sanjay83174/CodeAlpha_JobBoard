from django.urls import path
from .views import (
    EmployerRegisterView,
    CandidateRegisterView,
    LoginView,
    JobListCreateView,
    JobDetailView,
    ResumeUploadView,
    JobApplyView,
    MyApplicationsView,
    JobApplicationsView,
    ApplicationStatusUpdateView,
    NotificationListView,
    AdminStatsView,
)

urlpatterns = [
    path('register/employer/', EmployerRegisterView.as_view(), name='register-employer'),
    path('register/candidate/', CandidateRegisterView.as_view(), name='register-candidate'),
    path('login/', LoginView.as_view(), name='login'),
    path('jobs/', JobListCreateView.as_view(), name='job-list-create'),
    path('jobs/<int:pk>/', JobDetailView.as_view(), name='job-detail'),
    path('resume/upload/', ResumeUploadView.as_view(), name='resume-upload'),
    path('jobs/<int:pk>/apply/', JobApplyView.as_view(), name='job-apply'),
    path('my-applications/', MyApplicationsView.as_view(), name='my-applications'),
    path('jobs/<int:pk>/applications/', JobApplicationsView.as_view(), name='job-applications'),
    path('applications/<int:pk>/status/', ApplicationStatusUpdateView.as_view(), name='application-status-update'),
    path('notifications/', NotificationListView.as_view(), name='notifications'),
    path('stats/', AdminStatsView.as_view(), name='admin-stats'),
]
