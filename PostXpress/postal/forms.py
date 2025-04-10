from django.core.exceptions import ValidationError
from .models import Parcel, ParcelType, PaymentType, Station, IncidentReport
from django import forms


class ParcelForm(forms.ModelForm):
    class Meta:
        model = Parcel
        fields = [  'sender_name', 'sender_phone', 'sender_email', 'origin_location', 'sender_POBOX', 
                    'sender_address', 'receiver_name', 'receiver_phone', 'receiver_email', 'destination',
                    'receiver_POBOX','receiver_address', 'parcel_type', 'payment_type', 'description', 
                    'delivery_to_address'
        ]
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)        
        super(ParcelForm, self).__init__(*args, **kwargs)
        self.fields['parcel_type'].queryset = ParcelType.objects.all()
        self.fields['payment_type'].queryset = PaymentType.objects.all()
        
        # Ensure that stations are displayed in alphabetical order by office
        self.fields['origin_location'].queryset = Station.objects.order_by('office')
        self.fields['destination'].queryset = Station.objects.order_by('office')

        # Optional delivery fields
        self.fields['sender_email'].required = False
        self.fields['sender_POBOX'].required = False
        self.fields['sender_address'].required = False
        self.fields['receiver_email'].required = False
        self.fields['receiver_POBOX'].required = False
        self.fields['receiver_address'].required = False
        self.fields['delivery_to_address'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['sender_phone'].widget.attrs.update({
            'pattern': '254\\d{9}',
            'maxlength': '12',
            'placeholder': 'Enter phone number (e.g., 254XXXXXXXXX)',
            'title': 'Phone number must start with "254" and be exactly 12 digits long',
        })
        self.fields['receiver_phone'].widget.attrs.update({
            'pattern': '254\\d{9}',
            'maxlength': '12',
            'placeholder': 'Enter phone number (e.g., 254XXXXXXXXX)',
            'title': 'Phone number must start with "254" and be exactly 12 digits long',
        })
        

class ParcelStatusUpdateForm(forms.ModelForm):
    STATUS_CHOICES = [
        ('Registered', 'Registered'),
        ('Ready for dispatch', 'Ready for dispatch'),
        ('Dispatched', 'Dispatched'),
        ('In transit', 'In transit'),
        ('Delivered', 'Delivered'),
        ('Received', 'Received'),
        ('Under incidence', 'Under incidence'),
    ]
    status = forms.ChoiceField(choices=STATUS_CHOICES, label="Parcel Status")
    class Meta:
        model = Parcel
        fields = ['status']


class IncidentReportForm(forms.ModelForm):
    class Meta:
        model = IncidentReport
        fields = ['parcel', 'driver', 'vehicle', 'description', 'files']  # Fields that are part of the form
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_files(self):
        file = self.cleaned_data.get('files', False)
        if file:
            if file.size > 4 * 1024 * 1024:  # Limit file size to 4MB
                raise forms.ValidationError("File size should not exceed 4MB.")
            if not file.name.endswith(('.jpg', '.png', '.pdf')):
                raise forms.ValidationError("Only .jpg, .png, and .pdf files are allowed.")
        return file