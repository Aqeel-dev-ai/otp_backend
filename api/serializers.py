from rest_framework import serializers
from .models import OTPVerification

class OTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=15)

class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)

class OTPVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTPVerification
        fields = ['email', 'phone', 'otp', 'created_at', 'is_verified', 'expires_at'] 