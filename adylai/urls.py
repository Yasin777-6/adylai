"""
URL configuration for adylai project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Main platform
    path('register/', include('lawyers.urls')),  # Registration and dashboard
    path('website/', include('website_builder.urls')),
    path('leads/', include('leads.urls')),
    path('chat/', include('chatbot.urls')),
    
    # API endpoints
    path('api/', include([
        path('chat/', include('chatbot.api_urls')),
        path('leads/', include('leads.api_urls')),
        path('website/', include('website_builder.api_urls')),
    ])),
    
    # Home page
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    
    # Public website pages (should be last to catch lawyer slugs)
    path('<slug:lawyer_slug>/', include('website_builder.public_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site configuration
admin.site.site_header = "Lawyer Website Builder"
admin.site.site_title = "Lawyer Platform"
admin.site.index_title = "Welcome to Lawyer Platform Administration"
