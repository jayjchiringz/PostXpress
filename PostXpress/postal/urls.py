from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from django.urls import path, include

from .views import (
    ParcelListCreateView, ParcelDetailView, ParcelEventListCreateView, reports_view,
    SignupView, customer_dashboard, register_parcel, track_parcel, staff_incident_report,
    StaffDashboardView, StaffParcelManagementView, home, dashboard, parcel_detail_view, scan_qr_code,
    test_map_view
)

from . import views 

# Updated urlpatterns
urlpatterns = [
    path('', home, name='home'),  # Home view

    # Parcel-related views (API)
    path('api/parcels/', ParcelListCreateView.as_view(), name='parcel-list-create'),
    path('api/parcels/<str:tracking_number>/', ParcelDetailView.as_view(), name='api-parcel-detail'),
    path('parcels/<str:tracking_number>/receipt/', views.generate_receipt, name='generate_receipt'),
    path('update-status/', views.update_parcel_status, name='update_parcel_status'),
    path('scan/', TemplateView.as_view(template_name="scan.html"), name='scan_qr_code_page'),
    path('scan_qr_code/', views.scan_qr_code, name='scan_qr_code'),

    # Parcel-related views (HTML)
    path('parcels/<str:tracking_number>/events/', parcel_detail_view, name='parcel-events'),  # HTML parcel detail view
    path('parcel-events/', ParcelEventListCreateView.as_view(), name='parcel-event-list-create'),
    path('make-payment/<str:tracking_number>/', views.make_payment, name='make_payment'),
    path('report-incident/', views.report_incident, name='report_incident'),

    # Authentication views
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Customer-related views
    path('customer-dashboard/', views.staff_dashboard, name='customer_dashboard'),  # Changed this to 'customer-dashboard'
    path('dashboard/', dashboard, name='dashboard'),  # Retained 'dashboard'
    path('register-parcel/', register_parcel, name='register_parcel'),
    path('track-parcel/', views.track_parcel, name='parcel_tracking'),

    # Staff-related views
    path('staff-dashboard/', StaffDashboardView.as_view(), name='staff_dashboard'),
    path('staff/manage-parcel/<str:tracking_number>/', StaffParcelManagementView.as_view(), name='staff_manage_parcel'),    path('payment-history/', views.payment_history, name='payment_history'), 
    path('reports/', views.reports_view, name='reports'),
    path('staff/incident-report/', staff_incident_report, name='staff_incident_report'),
 
    # Other URL patterns
    path('contact/', views.contact, name='contact'),  # Add this line for the contact page
    path('faq/', views.faq, name='faq'),

    # Django's built-in authentication system URLs
    path('accounts/', include('django.contrib.auth.urls')),
    
    path('map-test/', test_map_view, name='map_test'),    
]
