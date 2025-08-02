from django.http import JsonResponse
from django.views.generic import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class LeadListAPIView(APIView):
    """List leads API"""
    
    def get(self, request):
        return Response({'message': 'Leads list API'})


class CreateLeadAPIView(APIView):
    """Create lead API"""
    
    def post(self, request):
        return Response({'message': 'Lead created'})


class LeadDetailAPIView(APIView):
    """Lead detail API"""
    
    def get(self, request, lead_id):
        return Response({'message': f'Lead {lead_id} API'})


class UpdateLeadAPIView(APIView):
    """Update lead API"""
    
    def put(self, request, lead_id):
        return Response({'message': f'Lead {lead_id} updated'})


class ConsultationListAPIView(APIView):
    """Consultation list API"""
    
    def get(self, request):
        return Response({'message': 'Consultations list API'})


class CreateConsultationAPIView(APIView):
    """Create consultation API"""
    
    def post(self, request):
        return Response({'message': 'Consultation created'})


class ConsultationDetailAPIView(APIView):
    """Consultation detail API"""
    
    def get(self, request, consultation_id):
        return Response({'message': f'Consultation {consultation_id} API'})


class LeadAnalyticsAPIView(APIView):
    """Lead analytics API"""
    
    def get(self, request):
        return Response({'message': 'Lead analytics API'})


class LeadSourcesAPIView(APIView):
    """Lead sources API"""
    
    def get(self, request):
        return Response({'message': 'Lead sources API'})


class PublicLeadCaptureAPIView(APIView):
    """Public lead capture API"""
    
    def post(self, request):
        return Response({'message': 'Lead captured from public form'}) 