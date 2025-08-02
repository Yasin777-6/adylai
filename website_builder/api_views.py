from django.http import JsonResponse
from django.views.generic import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class WebsiteContentAPIView(APIView):
    """Get website content"""
    
    def get(self, request):
        return Response({'message': 'Website content API'})


class SaveWebsiteAPIView(APIView):
    """Save website content"""
    
    def post(self, request):
        return Response({'message': 'Website saved'})


class PublishWebsiteAPIView(APIView):
    """Publish website"""
    
    def post(self, request):
        return Response({'message': 'Website published'})


class PageAPIView(APIView):
    """Page management API"""
    
    def get(self, request):
        return Response({'message': 'Pages API'})


class PageDetailAPIView(APIView):
    """Page detail API"""
    
    def get(self, request, page_id):
        return Response({'message': f'Page {page_id} API'})


class AssetAPIView(APIView):
    """Asset management API"""
    
    def get(self, request):
        return Response({'message': 'Assets API'})


class AssetUploadAPIView(APIView):
    """Asset upload API"""
    
    def post(self, request):
        return Response({'message': 'Asset uploaded'})


class AnalyticsAPIView(APIView):
    """Analytics API"""
    
    def get(self, request):
        return Response({'message': 'Analytics API'}) 