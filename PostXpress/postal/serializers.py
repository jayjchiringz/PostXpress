from rest_framework import serializers
from .models import Parcel, ParcelEvent
from django.contrib.auth.models import User

class ParcelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parcel
        fields = '__all__'

    def validate_sender(self, value):
        # Check if the sender exists in the User model (since sender is related to User)
        if not User.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Sender with this ID does not exist.")
        return value


class ParcelEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParcelEvent
        fields = '__all__'
