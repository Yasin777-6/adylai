from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from django.http import Http404
from lawyers.models import Lawyer
from .models import Website


class LawyerWebsiteView(TemplateView):
    """Public view for individual lawyer websites"""
    template_name = 'website_builder/public_website.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lawyer_slug = kwargs.get('lawyer_slug')
        
        try:
            # Get lawyer by domain slug
            lawyer = get_object_or_404(Lawyer, domain_slug=lawyer_slug)
            
            # Get or create website for lawyer
            website, created = Website.objects.get_or_create(
                lawyer=lawyer,
                defaults={
                    'title': f"{lawyer.user.get_full_name()} - Legal Services",
                    'domain_slug': lawyer.domain_slug,
                    'is_published': True,
                    'status': 'published'
                }
            )
            
            # Default content if none exists
            default_content = {
                'hero_title': f"Professional Legal Services in Kyrgyzstan",
                'hero_subtitle': f"Experienced lawyer {lawyer.user.get_full_name()} providing comprehensive legal solutions for individuals and businesses.",
                'hero_cta': "Schedule Consultation",
                'about_title': f"About {lawyer.user.get_full_name()}",
                'about_text': lawyer.bio or "Professional lawyer with extensive experience in various areas of law. Committed to providing high-quality legal services to clients throughout Kyrgyzstan.",
                'services_title': "Legal Services",
                'services_description': "We provide comprehensive legal services to meet all your legal needs.",
                'contact_address': getattr(lawyer.firm, 'address', None) if lawyer.firm else "Bishkek, Kyrgyzstan",
                'primary_color': '#1e3a8a',
                'secondary_color': '#3b82f6',
            }
            
            # Merge with custom content
            content = website.content_data or {}
            for key, value in default_content.items():
                if key not in content:
                    content[key] = value
            
            context.update({
                'lawyer': lawyer,
                'website': website,
                'content': content,
            })
            
        except Lawyer.DoesNotExist:
            raise Http404("Lawyer not found")
            
        return context


# Simple placeholder views
class LawyerWebsiteAboutView(LawyerWebsiteView):
    template_name = 'website_builder/public_about.html'


class LawyerWebsiteServicesView(LawyerWebsiteView):
    template_name = 'website_builder/public_services.html'


class LawyerWebsiteContactView(LawyerWebsiteView):
    template_name = 'website_builder/public_contact.html'


class LawyerWebsiteBlogView(LawyerWebsiteView):
    template_name = 'website_builder/public_blog.html' 