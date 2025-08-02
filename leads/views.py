from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Lead, Consultation, LeadNote, LeadSource, LeadAnalytics
from lawyers.models import Lawyer


class LeadListView(LoginRequiredMixin, ListView):
    """List all leads for the current lawyer"""
    model = Lead
    template_name = 'leads/lead_list.html'
    context_object_name = 'leads'
    paginate_by = 20
    
    def get_queryset(self):
        return Lead.objects.filter(lawyer=self.request.user.lawyer_profile).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lawyer = self.request.user.lawyer_profile
        
        # Real statistics from database
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        total_leads = Lead.objects.filter(lawyer=lawyer).count()
        new_leads_this_week = Lead.objects.filter(lawyer=lawyer, created_at__date__gte=week_ago).count()
        
        scheduled_consultations = Consultation.objects.filter(
            lawyer=lawyer, 
            status__in=['scheduled', 'confirmed']
        ).count()
        
        consultations_today = Consultation.objects.filter(
            lawyer=lawyer,
            scheduled_time__date=today,
            status__in=['scheduled', 'confirmed']
        ).count()
        
        chat_leads = Lead.objects.filter(lawyer=lawyer, source='website_chat').count()
        
        # Conversion rate calculation
        total_consultations = Consultation.objects.filter(lawyer=lawyer).count()
        conversion_rate = round((total_consultations / total_leads * 100) if total_leads > 0 else 0, 1)
        
        context.update({
            'total_leads': total_leads,
            'new_leads_this_week': new_leads_this_week,
            'scheduled_consultations': scheduled_consultations,
            'consultations_today': consultations_today,
            'chat_leads': chat_leads,
            'conversion_rate': conversion_rate,
            'today_consultations': Consultation.objects.filter(
                lawyer=lawyer,
                scheduled_time__date=today,
                status__in=['scheduled', 'confirmed']
            ).order_by('scheduled_time')[:3],
            'recent_leads': Lead.objects.filter(lawyer=lawyer).order_by('-created_at')[:3]
        })
        return context


class LeadDetailView(LoginRequiredMixin, DetailView):
    """View individual lead details"""
    model = Lead
    template_name = 'leads/lead_detail.html'
    context_object_name = 'lead'
    
    def get_queryset(self):
        return Lead.objects.filter(lawyer=self.request.user.lawyer_profile)


class LeadEditView(LoginRequiredMixin, UpdateView):
    """Edit lead information"""
    model = Lead
    template_name = 'leads/lead_edit.html'
    fields = ['status', 'priority', 'legal_category', 'case_description', 'internal_notes']
    
    def get_queryset(self):
        return Lead.objects.filter(lawyer=self.request.user.lawyer_profile)
    
    def get_success_url(self):
        return reverse_lazy('leads:lead_detail', kwargs={'pk': self.object.pk})


class LeadDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a lead"""
    model = Lead
    template_name = 'leads/lead_confirm_delete.html'
    success_url = reverse_lazy('leads:lead_list')
    
    def get_queryset(self):
        return Lead.objects.filter(lawyer=self.request.user.lawyer_profile)


class ConsultationListView(LoginRequiredMixin, ListView):
    """List all consultations for the current lawyer"""
    model = Consultation
    template_name = 'leads/consultation_list.html'
    context_object_name = 'consultations'
    
    def get_queryset(self):
        return Consultation.objects.filter(lawyer=self.request.user.lawyer_profile).order_by('-scheduled_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lawyer = self.request.user.lawyer_profile
        today = timezone.now().date()
        
        # Real consultation data
        context.update({
            'today_consultations': Consultation.objects.filter(
                lawyer=lawyer,
                scheduled_time__date=today
            ).order_by('scheduled_time'),
            'upcoming_consultations': Consultation.objects.filter(
                lawyer=lawyer,
                scheduled_time__date__gt=today,
                status__in=['scheduled', 'confirmed']
            ).order_by('scheduled_time')[:5],
            'total_consultations': Consultation.objects.filter(lawyer=lawyer).count(),
            'completed_consultations': Consultation.objects.filter(lawyer=lawyer, status='completed').count(),
        })
        return context


class ConsultationCreateView(LoginRequiredMixin, CreateView):
    """Create new consultation"""
    model = Consultation
    template_name = 'leads/consultation_create.html'
    fields = ['lead', 'scheduled_time', 'duration', 'consultation_type', 'meeting_method', 'agenda']
    success_url = reverse_lazy('leads:consultation_list')
    
    def form_valid(self, form):
        form.instance.lawyer = self.request.user.lawyer_profile
        return super().form_valid(form)


class ConsultationDetailView(LoginRequiredMixin, DetailView):
    """View consultation details"""
    model = Consultation
    template_name = 'leads/consultation_detail.html'
    context_object_name = 'consultation'
    
    def get_queryset(self):
        return Consultation.objects.filter(lawyer=self.request.user.lawyer_profile)


class ConsultationEditView(LoginRequiredMixin, UpdateView):
    """Edit consultation"""
    model = Consultation
    template_name = 'leads/consultation_edit.html'
    fields = ['scheduled_time', 'duration', 'status', 'consultation_type', 'meeting_method', 'agenda', 'notes']
    
    def get_queryset(self):
        return Consultation.objects.filter(lawyer=self.request.user.lawyer_profile)
    
    def get_success_url(self):
        return reverse_lazy('leads:consultation_detail', kwargs={'pk': self.object.pk})


class LeadAnalyticsView(LoginRequiredMixin, TemplateView):
    """Analytics dashboard for leads"""
    template_name = 'leads/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lawyer = self.request.user.lawyer_profile
        
        # Real analytics from database
        today = timezone.now().date()
        month_ago = today - timedelta(days=30)
        
        # Lead statistics
        total_leads = Lead.objects.filter(lawyer=lawyer).count()
        leads_this_month = Lead.objects.filter(lawyer=lawyer, created_at__date__gte=month_ago).count()
        
        # Consultation statistics  
        total_consultations = Consultation.objects.filter(lawyer=lawyer).count()
        completed_consultations = Consultation.objects.filter(lawyer=lawyer, status='completed').count()
        
        # Conversion rate
        conversion_rate = round((total_consultations / total_leads * 100) if total_leads > 0 else 0, 1)
        
        # Lead sources
        lead_sources = Lead.objects.filter(lawyer=lawyer).values('source').annotate(count=Count('source')).order_by('-count')
        
        # Legal categories
        legal_categories = Lead.objects.filter(lawyer=lawyer).values('legal_category').annotate(count=Count('legal_category')).order_by('-count')
        
        # Calculate percentages for sources
        source_data = []
        for source in lead_sources:
            percentage = round((source['count'] / total_leads * 100) if total_leads > 0 else 0, 1)
            source_data.append({
                'source': source['source'],
                'count': source['count'],
                'percentage': percentage
            })
        
        # Calculate percentages for categories  
        category_data = []
        for category in legal_categories:
            percentage = round((category['count'] / total_leads * 100) if total_leads > 0 else 0, 1)
            category_data.append({
                'category': category['legal_category'],
                'count': category['count'],
                'percentage': percentage
            })
        
        # Revenue calculation (basic)
        revenue_this_month = completed_consultations * float(lawyer.consultation_fee or 0)
        
        # AI chat performance
        chat_leads = Lead.objects.filter(lawyer=lawyer, source='website_chat').count()
        chat_conversion = round((chat_leads / total_leads * 100) if total_leads > 0 else 0, 1)
        
        context.update({
            'total_leads': total_leads,
            'leads_this_month': leads_this_month,
            'conversion_rate': conversion_rate,
            'chat_conversion': chat_conversion,
            'revenue_this_month': revenue_this_month,
            'source_data': source_data,
            'category_data': category_data,
            'total_consultations': total_consultations,
            'completed_consultations': completed_consultations,
        })
        return context


class LeadNoteCreateView(LoginRequiredMixin, CreateView):
    """Create a note for a lead"""
    model = LeadNote
    template_name = 'leads/note_create.html'
    fields = ['note_type', 'title', 'content']
    
    def form_valid(self, form):
        form.instance.lead_id = self.kwargs['lead_id']
        form.instance.author = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('leads:lead_detail', kwargs={'pk': self.kwargs['lead_id']})
