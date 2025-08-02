from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View, CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Lawyer, LawFirm, Subscription
from .forms import LawyerRegistrationForm, LawyerProfileForm


class LawyerRegistrationView(CreateView):
    """Registration view for new lawyers"""
    form_class = LawyerRegistrationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('lawyers:registration_success')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Login the user automatically after registration
        login(self.request, self.object)
        messages.success(self.request, 'Registration successful! Welcome to the platform.')
        return response


class RegistrationSuccessView(TemplateView):
    """Registration success page"""
    template_name = 'registration/registration_success.html'


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard for lawyers with real data"""
    template_name = 'lawyers/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            lawyer = self.request.user.lawyer_profile
            
            # Import here to avoid circular imports
            from leads.models import Lead, Consultation
            
            # Real data from database
            today = timezone.now().date()
            
            # Lead statistics
            total_leads = Lead.objects.filter(lawyer=lawyer).count()
            
            # Consultation statistics
            total_consultations = Consultation.objects.filter(lawyer=lawyer).count()
            today_consultations = Consultation.objects.filter(
                lawyer=lawyer,
                scheduled_time__date=today,
                status__in=['scheduled', 'confirmed']
            ).order_by('scheduled_time')
            scheduled_today = today_consultations.count()
            
            # Recent leads (last 3)
            recent_leads = Lead.objects.filter(lawyer=lawyer).order_by('-created_at')[:3]
            
            context.update({
                'lawyer': lawyer,
                'total_leads': total_leads,
                'total_consultations': total_consultations,
                'scheduled_today': scheduled_today,
                'today_consultations': today_consultations,
                'recent_leads': recent_leads,
                'website_published': lawyer.website_published,
                'website_url': f"http://127.0.0.1:8000/{lawyer.domain_slug}/" if lawyer.website_published else None,
            })
            
            # Website status
            if hasattr(lawyer, 'website'):
                context['website'] = lawyer.website
            else:
                context['website'] = None
                
        except Lawyer.DoesNotExist:
            # Create lawyer profile if it doesn't exist
            Lawyer.objects.create(user=self.request.user)
            context['lawyer'] = self.request.user.lawyer_profile
            context.update({
                'total_leads': 0,
                'total_consultations': 0,
                'scheduled_today': 0,
                'today_consultations': [],
                'recent_leads': [],
            })
            
        return context


class PublishWebsiteView(LoginRequiredMixin, View):
    """Publish/unpublish the lawyer's website"""
    
    def post(self, request):
        try:
            lawyer = request.user.lawyer_profile
            action = request.POST.get('action')
            
            if action == 'publish':
                website = lawyer.publish_website()
                website_url = f"http://127.0.0.1:8000/{lawyer.domain_slug}/"
                messages.success(request, f'Website published successfully! Your AI chatbot is now active at {website_url}')
                return JsonResponse({
                    'success': True,
                    'published': True,
                    'website_url': website_url,
                    'message': 'Website published successfully!'
                })
            
            elif action == 'unpublish':
                lawyer.unpublish_website()
                messages.info(request, 'Website unpublished. AI chatbot is now inactive.')
                return JsonResponse({
                    'success': True,
                    'published': False,
                    'message': 'Website unpublished successfully!'
                })
            
            else:
                return JsonResponse({'success': False, 'error': 'Invalid action'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class ProfileView(LoginRequiredMixin, TemplateView):
    """Lawyer profile view"""
    template_name = 'lawyers/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lawyer'] = self.request.user.lawyer_profile
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Edit lawyer profile"""
    model = Lawyer
    form_class = LawyerProfileForm
    template_name = 'lawyers/profile_edit.html'
    success_url = reverse_lazy('lawyers:profile')
    
    def get_object(self):
        return self.request.user.lawyer_profile
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)


class SubscriptionView(LoginRequiredMixin, TemplateView):
    """Subscription management view"""
    template_name = 'lawyers/subscription.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lawyer = self.request.user.lawyer_profile
        context['lawyer'] = lawyer
        context['subscription'] = lawyer.subscription
        return context


class SubscriptionUpgradeView(LoginRequiredMixin, View):
    """Handle subscription upgrades"""
    
    def post(self, request):
        plan = request.POST.get('plan')
        if plan in ['basic', 'pro', 'premium']:
            # In a real implementation, this would integrate with a payment processor
            messages.success(request, f'Subscription upgraded to {plan}!')
        else:
            messages.error(request, 'Invalid subscription plan.')
        return redirect('lawyers:subscription')


class SettingsView(LoginRequiredMixin, TemplateView):
    """General settings view"""
    template_name = 'lawyers/settings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lawyer'] = self.request.user.lawyer_profile
        return context
