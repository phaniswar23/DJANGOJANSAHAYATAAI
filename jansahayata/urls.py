"""
JanSahayata AI Master URL Configuration
Exposes REST APIs, Media Uploads, and serves pure native Django templates.
"""

import os
from datetime import datetime, timezone
from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse, FileResponse
from django.shortcuts import render
from django.urls import path, include, re_path
from django.views.static import serve
from django.views.generic.base import RedirectView
from django.conf.urls.static import static
from apps.complaints import views as complaint_views

def favicon_ico(request):
    path_ico = settings.BASE_DIR / 'static' / 'images' / 'favicon.ico'
    if os.path.exists(path_ico):
        return FileResponse(open(path_ico, 'rb'), content_type='image/x-icon')
    return JsonResponse({'error': 'Favicon not found'}, status=404)

def favicon_png(request):
    path_png = settings.BASE_DIR / 'static' / 'images' / 'favicon.png'
    if os.path.exists(path_png):
        return FileResponse(open(path_png, 'rb'), content_type='image/png')
    return JsonResponse({'error': 'Favicon not found'}, status=404)

def health_check(request):
    return JsonResponse({
        'status': 'online',
        'service': 'JanSahayata Grievance Intelligence Platform Backend (100% Pure Django Full-Stack)',
        'version': '2.0.0-django-templates',
        'database': 'SQLite (db.sqlite3)',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })

# Native Django View Renderers
def page_home(request):
    return render(request, 'citizen/home.html')

def page_citizen_login(request):
    return render(request, 'auth/citizen_login.html')

def page_citizen_register(request):
    return render(request, 'auth/citizen_register.html')

def page_staff_login(request):
    return render(request, 'auth/staff_login.html')

def page_forgot_password(request):
    return render(request, 'auth/forgot_password.html')

def page_report_problem(request):
    return render(request, 'citizen/report_problem.html')

def page_track_complaint(request):
    return render(request, 'citizen/track_complaint.html')

def page_complaint_details(request, id=None):
    return render(request, 'citizen/complaint_details.html')

def page_citizen_dashboard(request):
    return render(request, 'citizen/dashboard.html')

def page_my_complaints(request):
    return render(request, 'citizen/dashboard.html')

def page_staff_dashboard(request):
    return render(request, 'staff/dashboard.html')

def page_staff_complaints(request):
    return render(request, 'staff/dashboard.html')

def page_admin_dashboard(request):
    return render(request, 'admin_portal/dashboard.html')

def page_help(request):
    return render(request, 'citizen/help.html')

urlpatterns = [
    # Direct Favicon Routes (Binary stream for instant browser recognition)
    path('favicon.ico', favicon_ico, name='favicon_ico'),
    path('favicon.png', favicon_png, name='favicon_png'),

    # Super Admin Pages
    path('admin/dashboard', page_admin_dashboard, name='admin_dashboard'),
    path('admin/dashboard/', page_admin_dashboard),

    path('admin/', admin.site.urls),

    # 1. Primary Page Routes (Native Django Templates)
    path('', page_home, name='home'),
    path('login', page_citizen_login, name='citizen_login'),
    path('login/', page_citizen_login),
    path('register', page_citizen_register, name='citizen_register'),
    path('register/', page_citizen_register),
    path('staff/login', page_staff_login, name='staff_login'),
    path('staff/login/', page_staff_login),
    path('forgot-password', page_forgot_password, name='forgot_password'),
    path('forgot-password/', page_forgot_password),
    
    # Citizen Grievance Pages
    path('report', page_report_problem, name='report_problem'),
    path('report/', page_report_problem),
    path('report-problem', page_report_problem),
    path('report-problem/', page_report_problem),
    path('track', page_track_complaint, name='track_complaint'),
    path('track/', page_track_complaint),
    path('track-complaint', page_track_complaint),
    path('track-complaint/', page_track_complaint),
    path('complaint/<str:id>', page_complaint_details, name='complaint_details'),
    path('complaint/<str:id>/', page_complaint_details),
    path('citizen/dashboard', page_citizen_dashboard, name='citizen_dashboard'),
    path('citizen/dashboard/', page_citizen_dashboard),
    path('my-complaints', page_my_complaints, name='my_complaints'),
    path('my-complaints/', page_my_complaints),
    path('help', page_help, name='help'),
    path('help/', page_help),

    # Staff / Officer Pages
    path('staff/dashboard', page_staff_dashboard, name='staff_dashboard'),
    path('staff/dashboard/', page_staff_dashboard),
    path('staff/complaints', page_staff_complaints, name='staff_complaints'),
    path('staff/complaints/', page_staff_complaints),
    path('railway-dashboard', page_staff_dashboard),
    path('railway-dashboard/', page_staff_dashboard),

    # 2. REST API Endpoints
    path('api/auth/', include('apps.authentication.urls')),
    path('api/complaints', complaint_views.create_complaint, name='complaint_create_noslash'),
    path('api/complaints/', include('apps.complaints.urls')),
    path('api/staff/', include('apps.staff.urls')),
    path('api/admin/', include('apps.admin_portal.urls')),
    path('api/railway/', include('apps.railway.urls')),
    path('api/ai/', include('apps.ai_service.urls')),
    path('api/health', health_check, name='api_health'),

    # 3. Media & Uploads Serving
    re_path(r'^uploads/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

# 4. Explicit Static Files Serving in Development
urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static')
