from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # Chatbot management
    path('', views.ChatbotDashboardView.as_view(), name='dashboard'),
    path('configuration/', views.ChatConfigurationView.as_view(), name='configuration'),
    path('sessions/', views.ChatSessionListView.as_view(), name='session_list'),
    path('sessions/<uuid:session_id>/', views.ChatSessionDetailView.as_view(), name='session_detail'),
    
    # Full-page chat interface
    path('interface/<slug:lawyer_slug>/', views.ChatInterfaceView.as_view(), name='chat_interface'),
    
    # Analytics
    path('analytics/', views.ChatAnalyticsView.as_view(), name='analytics'),
    path('feedback/', views.ChatFeedbackView.as_view(), name='feedback'),
] 