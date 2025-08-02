from django.urls import path
from . import views

app_name = 'website_builder'

urlpatterns = [
    # Main website builder
    path('', views.WebsiteBuilderDashboard.as_view(), name='dashboard'),
    path('edit/', views.WebsiteEditor.as_view(), name='edit'),
    path('preview/', views.WebsitePreview.as_view(), name='preview'),
    
    # Pages management
    path('pages/', views.PageListView.as_view(), name='page_list'),
    path('pages/create/', views.PageCreateView.as_view(), name='page_create'),
    path('pages/<int:pk>/edit/', views.PageEditView.as_view(), name='page_edit'),
    
    # Templates and themes
    path('templates/', views.TemplateListView.as_view(), name='template_list'),
    
    # Media assets
    path('assets/', views.AssetListView.as_view(), name='asset_list'),
    path('assets/upload/', views.AssetUploadView.as_view(), name='asset_upload'),
    
    # Analytics
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    
    # Settings
    path('settings/', views.SettingsView.as_view(), name='settings'),
] 