from django.urls import path
from . import public_views

app_name = 'public_website'

urlpatterns = [
    # Public website pages - all use the same template but different sections
    path('', public_views.LawyerWebsiteView.as_view(), name='home'),
    path('about/', public_views.LawyerWebsiteAboutView.as_view(), name='about'),
    path('services/', public_views.LawyerWebsiteServicesView.as_view(), name='services'),
    path('contact/', public_views.LawyerWebsiteContactView.as_view(), name='contact'),
    path('blog/', public_views.LawyerWebsiteBlogView.as_view(), name='blog'),
] 