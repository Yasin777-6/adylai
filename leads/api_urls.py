from django.urls import path
from . import api_views

app_name = 'leads_api'

urlpatterns = [
    # Lead API
    path('', api_views.LeadListAPIView.as_view(), name='lead_list'),
    path('create/', api_views.CreateLeadAPIView.as_view(), name='create_lead'),
    path('<int:lead_id>/', api_views.LeadDetailAPIView.as_view(), name='lead_detail'),
    path('<int:lead_id>/update/', api_views.UpdateLeadAPIView.as_view(), name='update_lead'),
    
    # Consultation API
    path('consultations/', api_views.ConsultationListAPIView.as_view(), name='consultation_list'),
    path('consultations/create/', api_views.CreateConsultationAPIView.as_view(), name='create_consultation'),
    path('consultations/<int:consultation_id>/', api_views.ConsultationDetailAPIView.as_view(), name='consultation_detail'),
    
    # Analytics API
    path('analytics/', api_views.LeadAnalyticsAPIView.as_view(), name='analytics'),
    path('sources/', api_views.LeadSourcesAPIView.as_view(), name='sources'),
    
    # Public lead capture (from contact forms)
    path('capture/', api_views.PublicLeadCaptureAPIView.as_view(), name='public_lead_capture'),
] 