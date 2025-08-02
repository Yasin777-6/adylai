from django.urls import path
from . import views

app_name = 'lawyers'

urlpatterns = [
    # Registration
    path('register/', views.LawyerRegistrationView.as_view(), name='register'),
    path('registration-success/', views.RegistrationSuccessView.as_view(), name='registration_success'),
    
    # Main dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # Profile management
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    
    # Website publishing
    path('website/publish/', views.PublishWebsiteView.as_view(), name='publish_website'),
    
    # Subscription management
    path('subscription/', views.SubscriptionView.as_view(), name='subscription'),
    path('subscription/upgrade/', views.SubscriptionUpgradeView.as_view(), name='subscription_upgrade'),
    
    # Settings
    path('settings/', views.SettingsView.as_view(), name='settings'),
] 