from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, UpdateView
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from .models import ChatSession, ChatMessage, ChatConfiguration, ChatFeedback, ChatAnalytics
from lawyers.models import Lawyer


class ChatInterfaceView(TemplateView):
    """Full-page Telegram-style chat interface for visitors"""
    template_name = 'chatbot/chat_interface.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lawyer_slug = kwargs.get('lawyer_slug')
        
        # Get lawyer and ensure website is published
        lawyer = get_object_or_404(Lawyer, domain_slug=lawyer_slug, website_published=True)
        
        # Get service from URL parameter
        service = self.request.GET.get('service', '')
        
        context.update({
            'lawyer': lawyer,
            'service': service,
            'chat_config': {
                'lawyer_name': lawyer.full_name,
                'primary_language': lawyer.primary_language,
                'specialties': lawyer.specialties,
                'consultation_fee': lawyer.consultation_fee,
                'years_experience': lawyer.years_experience,
            }
        })
        return context


class ChatbotDashboardView(LoginRequiredMixin, TemplateView):
    """Main chatbot dashboard"""
    template_name = 'chatbot/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lawyer = self.request.user.lawyer_profile
        
        # Real chatbot statistics
        total_sessions = ChatSession.objects.filter(lawyer=lawyer).count()
        today_sessions = ChatSession.objects.filter(
            lawyer=lawyer, 
            started_at__date=timezone.now().date()
        ).count()
        
        # Lead generation from chat
        leads_generated = ChatSession.objects.filter(
            lawyer=lawyer, 
            consultation_requested=True
        ).count()
        
        # Calculate conversion rate
        conversion_rate = round((leads_generated / total_sessions * 100) if total_sessions > 0 else 0, 1)
        
        # Average response time
        avg_response_time = ChatMessage.objects.filter(
            session__lawyer=lawyer,
            message_type='assistant',
            response_time_ms__isnull=False
        ).aggregate(avg_time=Avg('response_time_ms'))['avg_time']
        
        avg_response_seconds = round(avg_response_time / 1000, 1) if avg_response_time else 0
        
        # User satisfaction from feedback
        avg_rating = ChatFeedback.objects.filter(
            session__lawyer=lawyer
        ).aggregate(avg_rating=Avg('rating'))['avg_rating']
        
        avg_rating = round(avg_rating, 1) if avg_rating else 0
        satisfaction_percentage = round((avg_rating / 5 * 100)) if avg_rating > 0 else 0
        
        # Recent conversations
        recent_sessions = ChatSession.objects.filter(lawyer=lawyer).order_by('-started_at')[:4]
        
        context.update({
            'total_conversations': total_sessions,
            'today_sessions': today_sessions,
            'leads_generated': leads_generated,
            'conversion_rate': conversion_rate,
            'avg_response_time': avg_response_seconds,
            'avg_rating': avg_rating,
            'satisfaction_percentage': satisfaction_percentage,
            'recent_sessions': recent_sessions,
            'chatbot_active': lawyer.website_published,
        })
        return context


class ChatConfigurationView(LoginRequiredMixin, TemplateView):
    """Chatbot configuration settings"""
    template_name = 'chatbot/configuration.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lawyer = self.request.user.lawyer_profile
        
        # Get or create chat configuration
        config, created = ChatConfiguration.objects.get_or_create(
            lawyer=lawyer,
            defaults={
                'ai_model': 'deepseek-chat',
                'max_tokens': 300,
                'temperature': 0.7,
                'collect_contact_info': True,
                'track_analytics': True
            }
        )
        
        context['config'] = config
        return context


class ChatSessionListView(LoginRequiredMixin, ListView):
    """List all chat sessions"""
    model = ChatSession
    template_name = 'chatbot/session_list.html'
    context_object_name = 'sessions'
    paginate_by = 20
    
    def get_queryset(self):
        return ChatSession.objects.filter(lawyer=self.request.user.lawyer_profile).order_by('-started_at')


class ChatSessionDetailView(LoginRequiredMixin, DetailView):
    """View individual chat session details"""
    model = ChatSession
    template_name = 'chatbot/session_detail.html'
    context_object_name = 'session'
    slug_field = 'session_id'
    slug_url_kwarg = 'session_id'
    
    def get_queryset(self):
        return ChatSession.objects.filter(lawyer=self.request.user.lawyer_profile)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['messages'] = ChatMessage.objects.filter(session=self.object).order_by('created_at')
        return context


class ChatAnalyticsView(LoginRequiredMixin, TemplateView):
    """Chatbot analytics dashboard"""
    template_name = 'chatbot/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lawyer = self.request.user.lawyer_profile
        
        # Time periods
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Real analytics data
        total_conversations = ChatSession.objects.filter(lawyer=lawyer).count()
        conversations_this_week = ChatSession.objects.filter(
            lawyer=lawyer, 
            started_at__date__gte=week_ago
        ).count()
        
        # Lead conversion analytics
        leads_generated = ChatSession.objects.filter(
            lawyer=lawyer, 
            consultation_requested=True
        ).count()
        
        conversion_rate = round((leads_generated / total_conversations * 100) if total_conversations > 0 else 0, 1)
        
        # Response time analytics
        response_times = ChatMessage.objects.filter(
            session__lawyer=lawyer,
            message_type='assistant',
            response_time_ms__isnull=False
        ).values_list('response_time_ms', flat=True)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        avg_response_seconds = round(avg_response_time / 1000, 1)
        
        # User satisfaction
        feedback = ChatFeedback.objects.filter(session__lawyer=lawyer)
        avg_satisfaction = feedback.aggregate(avg_rating=Avg('rating'))['avg_rating']
        avg_satisfaction = round(avg_satisfaction, 1) if avg_satisfaction else 0
        positive_feedback_count = feedback.filter(rating__gte=4).count()
        positive_percentage = round((positive_feedback_count / feedback.count() * 100)) if feedback.count() > 0 else 0
        
        # Most common topics/categories
        common_categories = ChatSession.objects.filter(lawyer=lawyer).exclude(
            legal_category__isnull=True
        ).values('legal_category').annotate(count=Count('legal_category')).order_by('-count')[:5]
        
        # Calculate topic percentages
        category_data = []
        for category in common_categories:
            percentage = round((category['count'] / total_conversations * 100) if total_conversations > 0 else 0, 1)
            category_data.append({
                'category': category['legal_category'],
                'count': category['count'],
                'percentage': percentage
            })
        
        # Peak hours analysis (simplified)
        sessions_by_hour = ChatSession.objects.filter(lawyer=lawyer).extra(
            select={'hour': 'EXTRACT(hour FROM started_at)'}
        ).values('hour').annotate(count=Count('id')).order_by('-count')[:3]
        
        context.update({
            'total_conversations': total_conversations,
            'conversations_this_week': conversations_this_week,
            'conversion_rate': conversion_rate,
            'leads_generated': leads_generated,
            'avg_response_time': avg_response_seconds,
            'avg_satisfaction': avg_satisfaction,
            'positive_percentage': positive_percentage,
            'category_data': category_data,
            'peak_hours': sessions_by_hour,
        })
        return context


class ChatFeedbackView(LoginRequiredMixin, ListView):
    """View chat feedback from users"""
    model = ChatFeedback
    template_name = 'chatbot/feedback.html'
    context_object_name = 'feedback_list'
    
    def get_queryset(self):
        return ChatFeedback.objects.filter(session__lawyer=self.request.user.lawyer_profile).order_by('-created_at')
