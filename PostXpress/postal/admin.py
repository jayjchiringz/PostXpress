from django.contrib import admin
from .models import Parcel, ParcelEvent, Customer, UserProfile, ParcelType, PaymentType, Driver, Vehicle


# Register your models here.
admin.site.register(Parcel)
admin.site.register(ParcelEvent)
admin.site.register(Customer)
admin.site.register(UserProfile)


@admin.register(ParcelType)
class ParcelTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'cost')
    search_fields = ('name',)
    list_filter = ('cost',)


# Check if Parcel is not already registered before registering it
if not admin.site.is_registered(Parcel):
    @admin.register(Parcel)
    class ParcelAdmin(admin.ModelAdmin):
        list_display = ['tracking_number', 'served_by', 'sender_name', 'receiver_name', 'origin_location', 'destination', 'status']


@admin.register(PaymentType)
class PaymentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'license_number', 'phone_number', 'available')
    search_fields = ('first_name', 'last_name', 'license_number', 'phone_number')

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'model', 'capacity', 'available')
    search_fields = ('plate_number', 'model')
