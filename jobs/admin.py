from django.contrib import admin
from .models import Employer, Candidate, Job, Application, Notification

@admin.register(Employer)
class EmployerAdmin(admin.ModelAdmin):
    list_display = ('id', 'company_name', 'user', 'website')
    search_fields = ('company_name', 'user__username', 'user__email')

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'user', 'phone')
    search_fields = ('full_name', 'user__username', 'user__email', 'skills')

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'employer', 'location', 'job_type', 'salary', 'is_active', 'created_at')
    list_filter = ('job_type', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'location', 'skills_required', 'employer__company_name')

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'candidate', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('job__title', 'candidate__full_name', 'candidate__user__username')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'message')
