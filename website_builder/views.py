from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from .models import Website, WebsitePage, WebsiteAsset
from lawyers.models import Lawyer


class WebsiteBuilderDashboard(LoginRequiredMixin, TemplateView):
    """Simple website builder dashboard"""
    template_name = 'website_builder/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lawyer = self.request.user.lawyer_profile
        
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
        
        context.update({
            'lawyer': lawyer,
            'website': website,
            'total_pages': 5,  # Standard pages: Home, About, Services, Contact, Blog
            'total_assets': WebsiteAsset.objects.filter(website=website).count(),
            'monthly_views': 234,  # Mock data for now
        })
        return context


class WebsiteEditor(LoginRequiredMixin, TemplateView):
    """Simple form-based website content editor"""
    template_name = 'website_builder/edit.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lawyer = self.request.user.lawyer_profile
        website, created = Website.objects.get_or_create(
            lawyer=lawyer,
            defaults={
                'title': f"{lawyer.user.get_full_name()} - Legal Services",
                'domain_slug': lawyer.domain_slug,
            }
        )
        context['website'] = website
        return context
    
    def post(self, request):
        """Handle website content updates"""
        try:
            lawyer = request.user.lawyer_profile
            website, created = Website.objects.get_or_create(lawyer=lawyer)
            
            # Update website content from form data
            content_data = {
                'hero_title': request.POST.get('hero_title', ''),
                'hero_subtitle': request.POST.get('hero_subtitle', ''),
                'hero_cta': request.POST.get('hero_cta', ''),
                'about_title': request.POST.get('about_title', ''),
                'about_text': request.POST.get('about_text', ''),
                'services_title': request.POST.get('services_title', ''),
                'services_description': request.POST.get('services_description', ''),
                'contact_address': request.POST.get('contact_address', ''),
                'primary_color': request.POST.get('primary_color', '#1e3a8a'),
                'secondary_color': request.POST.get('secondary_color', '#3b82f6'),
            }
            
            # Update website
            website.content_data = content_data
            website.title = content_data.get('hero_title', website.title)
            website.is_published = True
            website.save()
            
            # Also update lawyer profile
            lawyer.consultation_fee = request.POST.get('consultation_fee', lawyer.consultation_fee)
            lawyer.save()
            
            return JsonResponse({'success': True, 'message': 'Website updated successfully!'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class WebsitePreview(TemplateView):
    """Preview the lawyer's website"""
    template_name = 'website_builder/preview.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            lawyer = self.request.user.lawyer_profile
            website, created = Website.objects.get_or_create(lawyer=lawyer)
            context['website'] = website
            context['content'] = website.content_data or {}
        return context


# Simple placeholder views for the remaining URLs
class PageListView(LoginRequiredMixin, TemplateView):
    template_name = 'website_builder/pages.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pages'] = [
            {'name': 'Home', 'url': '/', 'status': 'Published'},
            {'name': 'About', 'url': '/about/', 'status': 'Published'},
            {'name': 'Services', 'url': '/services/', 'status': 'Published'},
            {'name': 'Contact', 'url': '/contact/', 'status': 'Published'},
            {'name': 'Blog', 'url': '/blog/', 'status': 'Draft'},
        ]
        return context


class PageCreateView(LoginRequiredMixin, TemplateView):
    template_name = 'website_builder/page_form.html'


class PageEditView(LoginRequiredMixin, TemplateView):
    template_name = 'website_builder/page_form.html'


class TemplateListView(LoginRequiredMixin, TemplateView):
    template_name = 'website_builder/templates.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['templates'] = [
            {'name': 'Professional Blue', 'preview': 'blue-theme.jpg', 'active': True},
            {'name': 'Modern Gray', 'preview': 'gray-theme.jpg', 'active': False},
            {'name': 'Dark Professional', 'preview': 'dark-theme.jpg', 'active': False},
        ]
        return context


class AssetListView(LoginRequiredMixin, TemplateView):
    template_name = 'website_builder/assets.html'


class AssetUploadView(LoginRequiredMixin, TemplateView):
    template_name = 'website_builder/upload.html'


class AnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'website_builder/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = {
            'total_views': 1250,
            'unique_visitors': 890,
            'bounce_rate': 35.2,
            'avg_session': '2:34',
        }
        return context


class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'website_builder/settings.html'
