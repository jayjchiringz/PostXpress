import datetime
import barcode
import pdfkit
import base64
import random
import qrcode
import json
import io

from barcode.writer import ImageWriter
from twilio.rest import Client
from celery import shared_task
from PIL import Image

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, status

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import Group, User
from django.contrib.auth.forms import UserCreationForm
from django.utils.decorators import method_decorator
from django.template.loader import render_to_string
from django.contrib.auth import login
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Count
from django.contrib import messages
from django.utils import timezone
from django.views import View
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse, JsonResponse
from django.db import models
from django import forms

from .serializers import ParcelSerializer, ParcelEventSerializer
from .payments import initiate_mpesa_payment
from .models import Parcel, ParcelEvent, PaymentInfo, PaymentType, Station, User, UserProfile, Driver, Vehicle, Schedule, IncidentReport
from .forms import ParcelForm, ParcelStatusUpdateForm, IncidentReportForm
from .utils import send_sms


# ===============================
# Customer & Staff Views
# ===============================
@login_required
def report_incident(request):
    if request.method == 'POST':
        parcel_id = request.POST.get('parcel')
        vehicle_id = request.POST.get('vehicle')  # Can be None
        driver_id = request.POST.get('driver')  # Can be None
        description = request.POST.get('description')

        # Retrieve the parcel, vehicle, and driver (if selected)
        parcel = Parcel.objects.get(id=parcel_id)
        vehicle = Vehicle.objects.get(id=vehicle_id) if vehicle_id else None
        driver = Driver.objects.get(id=driver_id) if driver_id else None

        # Create the incident report
        incident = IncidentReport.objects.create(
            parcel=parcel,
            vehicle=vehicle,
            driver=driver,
            description=description,
            reported_by=request.user
        )

        # Update the parcel's status to "Under incidence"
        parcel.status = 'Under incidence'
        parcel.save()

        # Show success message and redirect
        messages.success(request, "Incident reported successfully.")
        return redirect('report_incident')  # Redirect to a relevant view after submission

    # This handles the GET request to render the form
    parcels = Parcel.objects.all()
    vehicles = Vehicle.objects.all()
    drivers = Driver.objects.all()

    # Define the context to pass to the template
    context = {
        'parcels': parcels,
        'vehicles': vehicles,
        'drivers': drivers
    }

    return render(request, 'report_incident.html', context)


def home(request):
    return render(request, 'home.html')


# List/Create Parcels
class ParcelListCreateView(generics.ListCreateAPIView):
    queryset = Parcel.objects.all()
    serializer_class = ParcelSerializer

# Retrieve/Update Parcel
class ParcelDetailView(generics.RetrieveUpdateAPIView):
    queryset = Parcel.objects.all()
    serializer_class = ParcelSerializer
    lookup_field = 'tracking_number'

# List/Create Parcel Events
class ParcelEventListCreateView(generics.ListCreateAPIView):
    queryset = ParcelEvent.objects.all()
    serializer_class = ParcelEventSerializer
    
class ParcelCreate(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ParcelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@login_required
def reports_view(request):
    # Fetch filter parameters from GET request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    destination_id = request.GET.get('destination')  # This will be an ID from the dropdown
    origin_id = request.GET.get('origin')  # This will be an ID from the dropdown
    served_by_username = request.GET.get('served_by')

    # Initialize query
    parcels = Parcel.objects.select_related('origin_location', 'destination', 'served_by', 'parcel_type').all()

    # Filter by date range
    if start_date:
        parcels = parcels.filter(created_at__gte=start_date)
    if end_date:
        parcels = parcels.filter(created_at__lte=end_date)

    # Filter by destination (use the foreign key name directly)
    if destination_id:
        parcels = parcels.filter(destination__id=destination_id)

    # Filter by origin (use the foreign key name directly)
    if origin_id:
        parcels = parcels.filter(origin_location__id=origin_id)

    # Filter by served_by
    if served_by_username:
        parcels = parcels.filter(served_by__username=served_by_username)

    # Get all stations for the dropdowns
    destinations = Station.objects.all().order_by('office')
    origins = Station.objects.all().order_by('office')
    served_by_users = User.objects.all()

    # Render the template with the filtered parcels and options for filtering
    context = {
        'parcels': parcels,
        'destinations': destinations,
        'origins': origins,
        'served_by_users': served_by_users,
        'start_date': start_date,
        'end_date': end_date,
        'selected_destination': int(destination_id) if destination_id else None,
        'selected_origin': int(origin_id) if origin_id else None,
        'selected_served_by': served_by_username,
    }
    return render(request, 'reports.html', context)


@login_required
def generate_receipt(request, tracking_number):
    parcel = get_object_or_404(Parcel, tracking_number=tracking_number)

    # URL for real-time parcel tracking
    tracking_url = request.build_absolute_uri(reverse('parcel_tracking')) + f"?tracking_number={parcel.tracking_number}"

    # Generate QR code for tracking URL
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(tracking_url)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    img = qrcode.make(tracking_url)
    img = img.resize((100, 100))  # Set to a smaller size

    # Save QR code image to a byte stream
    byte_io = io.BytesIO()
    img.save(byte_io, format='PNG')
    byte_io.seek(0)

    # Convert the byte stream into a base64 encoded string
    qr_code_base64 = base64.b64encode(byte_io.read()).decode('utf-8')

    # Generate barcode for tracking number
    barcode_io = io.BytesIO()
    EAN = barcode.get_barcode_class('code128')
    tracking_barcode = EAN(parcel.tracking_number, writer=ImageWriter())

    tracking_barcode.write(barcode_io, {
        'module_width': 0.15,
        'module_height': 2.0,
        'write_text': False 
    })
    barcode_io.seek(0)

    # Convert the barcode image to base64
    barcode_base64 = base64.b64encode(barcode_io.read()).decode('utf-8')
    
    # Payment info (replace with actual payment data)
    payment_info = {
        'amount': parcel.parcel_type.cost,
        'timestamp': timezone.now(),
        'status': 'Paid',
        'method': 'MPESA',
    }

    return render(request, 'parcel_receipt.html', {
        'parcel': parcel,
        'payment_info': payment_info,
        'qr_code_base64': qr_code_base64,  # Pass the QR code image as base64
        'barcode_base64': barcode_base64,  # Barcode image    
    })


def register_parcel_payment(parcel, amount, payment_method):
    payment = PaymentInfo.objects.create(
        parcel=parcel,
        amount=amount,
        payment_method=payment_method,
        payment_status='Completed'  # Assuming the payment is successful
    )
    payment.save()


@login_required
def make_payment(request, tracking_number):
    parcel = get_object_or_404(Parcel, tracking_number=tracking_number)
    amount = parcel.calculate_total_cost()

    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        # Format the phone number using the helper function before initiating payment

        try:
            amount = float(amount)
            
        except (TypeError, ValueError):
            messages.error(request, 'Invalid amount. Please enter a valid number.')
            return render(request, 'make_payment.html', {'parcel': parcel, 'amount': amount})

        # Set the payment method (could also be retrieved dynamically from the form)
        payment_method = request.POST.get('payment_method', 'MPESA')

        # Initiate MPESA payment
        payment_response = initiate_mpesa_payment(phone_number, amount)

        # Log the response for debugging
        print("Payment response:", json.dumps(phone_number, indent=4))

        # Check if the response is successful
        if payment_response and payment_response.get('ResponseCode') == '0':
            messages.success(request, 'Payment initiated successfully!')
            
            register_parcel_payment(parcel, amount, payment_method)
            
            # Send SMS notifications to sender and receiver
            message = (
                f"Parcel {parcel.tracking_number} registered successfully! "
                f"From: {parcel.origin_location}, To: {parcel.destination} "
                f"({parcel.receiver_name})"
            )
            response = send_sms([parcel.sender_phone, parcel.receiver_phone], message)
            
            if response is None:
                messages.error(request, "Failed to send SMS notification. Please try again.")

            return redirect('generate_receipt', tracking_number=tracking_number)
        else:
            # Log additional error details if available
            error_message = payment_response.get('errorMessage', 'Payment failed. Please try again.')
            print("Error message:", error_message)
            messages.error(request, error_message)

    return render(request, 'make_payment.html', {'parcel': parcel, 'amount': amount})


@login_required
def update_parcel_status(request):
    if request.method == 'POST':
        tracking_number = request.POST.get('tracking_number')
        parcel = get_object_or_404(Parcel, tracking_number=tracking_number)

        form = ParcelStatusUpdateForm(request.POST, instance=parcel)
        if form.is_valid():
            parcel = form.save(commit=False)
            previous_status = parcel.status
            new_status = form.cleaned_data['status']

            # Save the new status
            parcel.save()

            # Log the event only if the status changed
            if previous_status != new_status:
                ParcelEvent.objects.create(parcel=parcel, event_type=new_status, updated_by=request.user)

            # Redirect or show a success message
            return redirect('dashboard')

    else:
        form = ParcelStatusUpdateForm()

    return render(request, 'update_status.html', {'form': form})


@csrf_exempt
def scan_qr_code(request):
    """
    API endpoint that processes QR code scans and updates parcel status.
    """
    if request.method == 'POST':
        print(f"POST data: {request.POST}")
        tracking_number = request.POST.get('tracking_number')
        if not tracking_number:
            return JsonResponse({'error': 'No tracking number provided.'}, status=400)

        # Fetch the parcel using the tracking number
        parcel = get_object_or_404(Parcel, tracking_number=tracking_number)

        # Save the current status before updating
        previous_status = parcel.status

        # Determine the current status and update accordingly
        if parcel.status == 'Registered':
            parcel.status = 'Ready for Dispatch'
        elif parcel.status == 'Ready for Dispatch':
            parcel.status = 'Dispatched'
        elif parcel.status == 'Dispatched':
            parcel.status = 'In Transit'
        elif parcel.status == 'In Transit':
            parcel.status = 'Delivered'
        elif parcel.status == 'Delivered':
            parcel.status = 'Received'
        else:
            return JsonResponse({'error': 'Invalid status for this operation.'}, status=400)

        # Save the updated parcel status
        parcel.save()

        # Log the event if the status has changed
        if previous_status != parcel.status:
            ParcelEvent.objects.create(parcel=parcel, event_type=parcel.status)
        return JsonResponse({'success': f'Parcel {parcel.tracking_number} status updated to {parcel.status}.'})    
    return JsonResponse({'error': 'Invalid request method.'}, status=405)


@login_required
@permission_required('is_staff', raise_exception=True)
def staff_incident_report(request):
    # Dummy data for demonstration purposes
    reports = [
        {"id": 1, "description": "Lost parcel reported", "date": "2024-10-10"},
        {"id": 2, "description": "Damaged parcel reported", "date": "2024-10-11"},
    ]

    context = {
        'reports': reports
    }
    return render(request, 'staff_incident_report.html', context)


# ===============================
# User Authentication and Role Management
# ===============================        
# Signup view (updated)      
class SignupView(View):
    def get(self, request):
        form = UserCreationForm()
        return render(request, 'registration/signup.html', {'form': form})

    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Assign default role (e.g., 'customer') upon registration
            customer_group = Group.objects.get(name='customer')
            user.groups.add(customer_group)
            login(request, user)
            return redirect('dashboard')  # Redirect to dashboard after signup
        return render(request, 'registration/signup.html', {'form': form})
        
        
# ===============================
# Dashboard and Role-Based Views
# ===============================
# Customer dashboard
@login_required
def customer_dashboard(request):
    # Fetch parcels created by the logged-in user (Customer)
    parcels = Parcel.objects.filter(sender=request.user)
    return render(request, 'customer_dashboard.html', {'parcels': parcels})

# Staff dashboard
@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('is_staff'), name='dispatch')
class StaffDashboardView(View):
    def get(self, request):
        # Fetch all parcels for staff to manage
        parcels = Parcel.objects.all()
        return render(request, 'staff_dashboard.html', {'parcels': parcels})


@login_required
def staff_dashboard(request):
    # Fetch parcels processed by each staff member
    parcels_per_staff = Parcel.objects.select_related('served_by').all()
    
    # Drivers and their availability
    drivers = Driver.objects.all()

    # Vehicles and their availability
    vehicles = Vehicle.objects.all()

    # Parcel events for recent activity tracking
    recent_events = ParcelEvent.objects.select_related('parcel', 'updated_by').order_by('-timestamp')[:10]

    context = {
        'parcels_per_staff': parcels_per_staff,
        'drivers': drivers,
        'vehicles': vehicles,
        'recent_events': recent_events,
    }
    
    return render(request, 'staff_dashboard.html', context)


# ===============================
# Parcel Registration (Customer)
# ===============================
# Parcel registration form for customers

@login_required
def register_parcel(request):
    if request.method == 'POST':
        form = ParcelForm(request.POST)
        if form.is_valid():
            parcel = form.save(commit=False)
            parcel.served_by = request.user
            parcel.tracking_number = generate_tracking_number()
            parcel.status = 'Registered'
            
            # Determine if delivery is to a specific address and add delivery cost
            if form.cleaned_data.get('delivery_to_address'):
                parcel.delivery_to_address = True
                parcel.delivery_cost = 250  # Fixed delivery cost for home/office
            else:
                parcel.delivery_to_address = False
                parcel.delivery_cost = 0

            parcel.save()

            # Redirect to the payment page
            return redirect('make_payment', tracking_number=parcel.tracking_number)
    else:
        form = ParcelForm()
    
    return render(request, 'register_parcel.html', {'form': form})


# A helper function to generate a tracking number (you can customize this)
def generate_tracking_number():
    import uuid
    return 'PX' + str(uuid.uuid4())[:10].replace('-', '').upper()

def parcel_detail_view(request, tracking_number):
    parcel = get_object_or_404(Parcel, tracking_number=tracking_number)
    events = parcel.events.order_by('-timestamp')  # Get all events related to the parcel

    return render(request, 'parcel_events.html', {
        'parcel': parcel,
        'events': events
    })


# ===============================
# Parcel Tracking (Staff/Customer)
# ===============================
@login_required
def track_parcel(request):
    tracking_number = request.GET.get('tracking_number')
    parcel = None
    events = None
    if tracking_number:
        try:
            # Fetch the parcel based on the tracking number
            parcel = Parcel.objects.get(tracking_number=tracking_number)
            parcel.update_location()
            events = ParcelEvent.objects.filter(parcel=parcel)
            
            # Convert Decimal to float
            parcel.current_latitude = float(parcel.current_latitude) if parcel.current_latitude else None
            parcel.current_longitude = float(parcel.current_longitude) if parcel.current_longitude else None
        except Parcel.DoesNotExist:
            # No parcel found, return None
            parcel = None
    
    # Render the template and pass parcel, events, and tracking number
    return render(request, 'track_parcel.html', {
        'parcel': parcel,
        'events': events,
        'tracking_number': tracking_number
    })       


@shared_task
def update_parcel_location(parcel_id):
    parcel = Parcel.objects.get(id=parcel_id)
    # If in transit, fetch and update the vehicle's current GPS location
    if parcel.status == "In Transit":
        # Retrieve the current location from the vehicle or delivery API
        current_lat, current_long = get_live_vehicle_location(parcel)
        parcel.current_latitude = current_lat
        parcel.current_longitude = current_long
    else:
        # Update based on station's coordinates
        parcel.update_location()
    parcel.save()
    
    
# ===============================
# Staff-Only View to Manage Parcel Status
# ===============================
@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('is_staff'), name='dispatch')
class StaffParcelManagementView(View):
    def get(self, request, tracking_number):
        parcel = get_object_or_404(Parcel, tracking_number=tracking_number)
        return render(request, 'staff_manage_parcel.html', {'parcel': parcel})

    def post(self, request, tracking_number):
        parcel = get_object_or_404(Parcel, tracking_number=tracking_number)
        # Update the parcel status by staff (In Transit, Delivered, etc.)
        new_status = request.POST.get('status')
        if new_status:
            parcel.status = new_status
            parcel.save()
        return redirect('staff_dashboard')


# ===============================
# API-Based Parcel Creation (existing)
# ===============================

@login_required
def dashboard(request):
    # Fetch parcels created by the logged-in user (Customer)
    parcels = Parcel.objects.filter(served_by=request.user)
    return render(request, 'dashboard.html', {'parcels': parcels})
    

def payment_history(request):
    # Total revenue: sum of all payments that are not pending
    total_revenue = PaymentInfo.objects.filter(payment_status='Completed').aggregate(Sum('amount'))['amount__sum'] or 0

    # Pending payments count
    pending_payments_count = PaymentInfo.objects.filter(payment_status='Pending').count()

    # Total parcels registered
    total_parcels = Parcel.objects.count()

    # Payment breakdown by method
    payment_by_method = PaymentInfo.objects.values('payment_method').annotate(total=Sum('amount')).order_by('-total')

    # Recent payments (last 10)
    recent_payments = PaymentInfo.objects.select_related('parcel').order_by('-transaction_date')[:10]

    context = {
        'total_revenue': total_revenue,
        'pending_payments_count': pending_payments_count,
        'total_parcels': total_parcels,
        'payment_by_method': payment_by_method,
        'recent_payments': recent_payments,
    }    
    return render(request, 'payment_history.html', context)
    

def contact(request):
    return render(request, 'contact.html')
    

def faq(request):
    return render(request, 'faq.html')    
    
    
def test_map_view(request):
    return render(request, 'map_test.html')
