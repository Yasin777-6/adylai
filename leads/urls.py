from django.urls import path
from django.views.generic import View
from . import views

app_name = 'leads'

urlpatterns = [
    # Lead management
    path('', views.LeadListView.as_view(), name='lead_list'),
    path('<int:pk>/', views.LeadDetailView.as_view(), name='lead_detail'),
    path('<int:pk>/edit/', views.LeadEditView.as_view(), name='lead_edit'),
    path('<int:pk>/delete/', views.LeadDeleteView.as_view(), name='lead_delete'),
    
    # Consultation management
    path('consultations/', views.ConsultationListView.as_view(), name='consultation_list'),
    path('consultations/create/', views.ConsultationCreateView.as_view(), name='consultation_create'),
    path('consultations/<int:pk>/', views.ConsultationDetailView.as_view(), name='consultation_detail'),
    path('consultations/<int:pk>/edit/', views.ConsultationEditView.as_view(), name='consultation_edit'),
    
    # Analytics
    path('analytics/', views.LeadAnalyticsView.as_view(), name='analytics'),
    
    # Lead notes
    path('<int:lead_id>/notes/create/', views.LeadNoteCreateView.as_view(), name='note_create'),
] 