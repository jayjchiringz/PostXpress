from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
from django.db import models

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()


class ParcelType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.name


class PaymentType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Station(models.Model):
    code = models.CharField(max_length=10, unique=True)
    office = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return f"{self.office} ({self.code})"

    class Meta:
        ordering = ['office']  # Sort stations alphabetically by office name


class Driver(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    license_number = models.CharField(max_length=50, unique=True)
    available = models.BooleanField(default=True)
    current_station = models.ForeignKey(Station, on_delete=models.SET_NULL, null=True, blank=True, related_name='drivers')

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.license_number})"


class Vehicle(models.Model):
    plate_number = models.CharField(max_length=20, unique=True)
    model = models.CharField(max_length=100)
    capacity = models.DecimalField(max_digits=10, decimal_places=2)  # Capacity in kg or other units
    available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.plate_number} - {self.model}"


class Parcel(models.Model):
    tracking_number = models.CharField(max_length=100, unique=True, editable=False)
    served_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='served_parcels')
    sender_phone = models.CharField(max_length=20, default='254')
    sender_email = models.EmailField(null=True, blank=True)
    sender_POBOX = models.CharField(max_length=50, null=True, blank=True)
    sender_address = models.CharField(max_length=200, null=True, blank=True)  
    sender_name = models.CharField(max_length=100)    

    description = models.CharField(max_length=255)
        
    receiver_name = models.CharField(max_length=100)
    receiver_phone = models.CharField(max_length=20, default='254')
    receiver_email = models.EmailField(null=True, blank=True)
    receiver_POBOX = models.CharField(max_length=50, null=True, blank=True)
    receiver_address = models.CharField(max_length=200, null=True, blank=True)

    status = models.CharField(max_length=50, default='Registered')

    origin_location = models.ForeignKey(Station, on_delete=models.SET_NULL, null=True, blank=True, related_name='origin_parcels')
    destination = models.ForeignKey(Station, on_delete=models.SET_NULL, null=True, blank=True, related_name='destination_parcels')

    delivery_to_address = models.BooleanField(default=False)  # True if the parcel is to be delivered to a specific address
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=250)  # Delivery fee to the address

    parcel_type = models.ForeignKey(ParcelType, on_delete=models.SET_NULL, null=True, blank=True, related_name='parcels')
    payment_type = models.ForeignKey(PaymentType, on_delete=models.SET_NULL, null=True, blank=True, related_name='parcels')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
  
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name='parcels')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='parcels')
    is_assigned = models.BooleanField(default=False) 

    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
  
    def calculate_total_cost(self):
        """
        Method to calculate the total cost of the parcel including delivery cost if applicable.
        """
        total_cost = self.parcel_type.cost
        if self.delivery_to_address:
            total_cost += 250           # delivery_cost Assume Kshs 250 delivery cost
        return total_cost

    def update_location(self):
        if self.status in ["Registered", "Ready for Dispatch"]:
            self.current_latitude = self.origin_location.latitude
            self.current_longitude = self.origin_location.longitude
        elif self.status == "Delivered":
            self.current_latitude = self.destination.latitude
            self.current_longitude = self.destination.longitude
        # Save these changes
        self.save()

    def __str__(self):
        return self.tracking_number
        
        
class ParcelEvent(models.Model):
    EVENT_CHOICES = [
        ('Registered', 'Registered'),
        ('Ready for dispatch', 'Ready for dispatch'),
        ('Dispatched', 'Dispatched'),
        ('In transit', 'In transit'),
        ('Delivered', 'Delivered'),
        ('Received', 'Received'),
        ('Under incidence', 'Under incidence'),
    ]

    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=50, choices=EVENT_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.parcel.tracking_number} - {self.event_type} at {self.timestamp}"


class Customer(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class PaymentInfo(models.Model):
    parcel = models.OneToOneField(Parcel, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=20, default='Pending')
    transaction_date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Payment for {self.parcel.tracking_number}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    def __str__(self):
        return f"{self.user.username}'s Profile"


class Schedule(models.Model):
    route_code = models.CharField(max_length=20)  # Code for route (e.g., NAI-MSA)
    origin_station = models.ForeignKey(Station, related_name='origin_schedules', on_delete=models.CASCADE)
    destination_station = models.ForeignKey(Station, related_name='destination_schedules', on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    departure_time = models.TimeField()  # Daily departure time for the route
    arrival_time = models.TimeField()  # Estimated arrival time
    schedule_date = models.DateField()  # Date for the schedule
    is_completed = models.BooleanField(default=False)  # Tracks if the job has been completed
    def __str__(self):
        return f"Route {self.origin_station.office} to {self.destination_station.office} on {self.schedule_date}"    
    class Meta:
        unique_together = ('origin_station', 'destination_station', 'schedule_date')  # Unique per day and route


class IncidentReport(models.Model):
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, related_name="incidents")
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()  # Description of the incident
    timestamp = models.DateTimeField(auto_now_add=True)  # Auto-populate with the current timestamp
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)  # The user reporting the incident
    files = models.FileField(upload_to='incident_files/', null=True, blank=True)  # File uploads, optional

    def __str__(self):
        return f"Incident for Parcel: {self.parcel.tracking_number} reported by {self.reported_by.username}"