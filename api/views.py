from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from .models import OTPVerification
from .serializers import OTPRequestSerializer, OTPVerifySerializer
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings
import logging
import ssl
import certifi
import os
import traceback

logger = logging.getLogger(__name__)

# Create your views here.

class SendOTPView(APIView):
    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            phone = serializer.validated_data['phone']

            # Create new OTP verification
            otp_verification = OTPVerification(email=email, phone=phone)
            otp_verification.save()

            # Send OTP via SendGrid
            try:
                # Set SSL certificate path
                os.environ['SSL_CERT_FILE'] = certifi.where()
                os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
                
                logger.info(f"Attempting to send email to {email} using SendGrid")
                logger.info(f"Using SendGrid API Key: {settings.SENDGRID_API_KEY[:5]}...")
                logger.info(f"Using From Email: {settings.FROM_EMAIL}")
                
                sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
                message = Mail(
                    from_email=settings.FROM_EMAIL,
                    to_emails=email,
                    subject='Your OTP Verification Code',
                    html_content=f'<p>Your OTP verification code is: <strong>{otp_verification.otp}</strong></p>'
                )
                response = sg.send(message)
                logger.info(f"SendGrid Response Status Code: {response.status_code}")
                logger.info(f"SendGrid Response Headers: {response.headers}")
                logger.info(f"SendGrid Response Body: {response.body}")
                
                return Response({
                    'message': 'OTP sent successfully',
                    'otp': otp_verification.otp,  # Including OTP in response for testing
                    'email': email,
                    'phone': phone
                }, status=status.HTTP_200_OK)
            except Exception as e:
                error_details = {
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'traceback': traceback.format_exc()
                }
                logger.error(f"SendGrid Error Details: {error_details}")
                otp_verification.delete()
                return Response({
                    'error': 'Failed to send OTP',
                    'details': str(e),
                    'email': email,
                    'phone': phone
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            phone = serializer.validated_data['phone']
            otp = serializer.validated_data['otp']

            try:
                otp_verification = OTPVerification.objects.get(
                    email=email,
                    phone=phone,
                    otp=otp,
                    is_verified=False
                )

                if otp_verification.is_expired():
                    return Response({
                        'error': 'OTP has expired'
                    }, status=status.HTTP_400_BAD_REQUEST)

                otp_verification.is_verified = True
                otp_verification.save()

                return Response({
                    'message': 'OTP verified successfully',
                    'email': email,
                    'phone': phone
                }, status=status.HTTP_200_OK)

            except ObjectDoesNotExist:
                return Response({
                    'error': 'Invalid OTP'
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
