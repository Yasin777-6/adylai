from django.urls import path
from . import api_views

app_name = 'website_builder_api'

urlpatterns = [
    # Website API
    path('content/', api_views.WebsiteContentAPIView.as_view(), name='website_content'),
    path('save/', api_views.SaveWebsiteAPIView.as_view(), name='save_website'),
    path('publish/', api_views.PublishWebsiteAPIView.as_view(), name='publish_website'),
    
    # Page API
    path('pages/', api_views.PageAPIView.as_view(), name='pages'),
    path('pages/<int:page_id>/', api_views.PageDetailAPIView.as_view(), name='page_detail'),
    
    # Asset API
    path('assets/', api_views.AssetAPIView.as_view(), name='assets'),
    path('assets/upload/', api_views.AssetUploadAPIView.as_view(), name='asset_upload'),
    
    # Analytics API
    path('analytics/', api_views.AnalyticsAPIView.as_view(), name='analytics'),
] 