from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
import uuid


class ChatSession(models.Model):
    """Chat session for visitor interactions"""
    SESSION_STATUS = [
        ('active', _('Active')),
        ('ended', _('Ended')),
        ('transferred', _('Transferred to Lawyer')),
    ]
    
    lawyer = models.ForeignKey('lawyers.Lawyer', on_delete=models.CASCADE, related_name='chat_sessions')
    session_id = models.UUIDField(_('Session ID'), default=uuid.uuid4, unique=True)
    visitor_name = models.CharField(_('Visitor Name'), max_length=100, blank=True)
    visitor_email = models.EmailField(_('Visitor Email'), blank=True)
    visitor_phone = models.CharField(_('Visitor Phone'), max_length=20, blank=True)
    visitor_ip = models.GenericIPAddressField(_('Visitor IP'), blank=True, null=True)
    
    # Session Information
    status = models.CharField(_('Status'), max_length=20, choices=SESSION_STATUS, default='active')
    language = models.CharField(_('Language'), max_length=5, default='ru')
    legal_category = models.CharField(_('Legal Category'), max_length=50, blank=True)
    
    # Consultation Request
    consultation_requested = models.BooleanField(_('Consultation Requested'), default=False)
    consultation_message = models.TextField(_('Consultation Message'), blank=True)
    preferred_contact_method = models.CharField(
        _('Preferred Contact Method'), 
        max_length=20, 
        choices=[('phone', _('Phone')), ('email', _('Email')), ('whatsapp', _('WhatsApp'))],
        blank=True
    )
    
    # Metadata
    user_agent = models.TextField(_('User Agent'), blank=True)
    referrer = models.URLField(_('Referrer'), blank=True)
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Chat Session')
        verbose_name_plural = _('Chat Sessions')
        ordering = ['-started_at']
    
    def __str__(self):
        name = self.visitor_name or f"Anonymous ({self.visitor_ip})"
        return f"{self.lawyer.full_name} - {name}"
    
    @property
    def duration(self):
        """Calculate session duration"""
        if self.ended_at:
            return self.ended_at - self.started_at
        return None
    
    @property
    def is_lead(self):
        """Check if session generated a lead"""
        return bool(self.visitor_email or self.visitor_phone or self.consultation_requested)


class ChatMessage(models.Model):
    """Individual chat messages within a session"""
    MESSAGE_TYPES = [
        ('user', _('User Message')),
        ('ai', _('AI Response')),
        ('system', _('System Message')),
        ('lawyer', _('Lawyer Message')),
    ]
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(_('Message Type'), max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField(_('Message Content'))
    
    # AI Response Metadata
    ai_model = models.CharField(_('AI Model'), max_length=50, blank=True)
    response_time_ms = models.PositiveIntegerField(_('Response Time (ms)'), blank=True, null=True)
    tokens_used = models.PositiveIntegerField(_('Tokens Used'), blank=True, null=True)
    
    # Message Status
    is_helpful = models.BooleanField(_('Marked as Helpful'), default=False)
    needs_review = models.BooleanField(_('Needs Review'), default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Chat Message')
        verbose_name_plural = _('Chat Messages')
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.session} - {self.message_type}: {self.content[:50]}..."


class ChatConfiguration(models.Model):
    """AI chat configuration for each lawyer"""
    lawyer = models.OneToOneField('lawyers.Lawyer', on_delete=models.CASCADE, related_name='chat_config')
    
    # AI Settings
    ai_model = models.CharField(_('AI Model'), max_length=50, default='deepseek-chat')
    system_prompt = models.TextField(_('System Prompt'), help_text=_('Instructions for the AI assistant'))
    max_tokens = models.PositiveIntegerField(_('Max Tokens'), default=500)
    temperature = models.FloatField(_('Temperature'), default=0.7)
    
    # Chat Behavior
    collect_contact_info = models.BooleanField(_('Collect Contact Info'), default=True)
    auto_suggest_consultation = models.BooleanField(_('Auto Suggest Consultation'), default=True)
    response_delay_seconds = models.PositiveIntegerField(_('Response Delay (seconds)'), default=1)
    
    # Greeting Messages
    welcome_message_ru = models.TextField(_('Welcome Message (Russian)'), blank=True)
    welcome_message_ky = models.TextField(_('Welcome Message (Kyrgyz)'), blank=True)
    welcome_message_en = models.TextField(_('Welcome Message (English)'), blank=True)
    
    # Business Hours
    office_hours_enabled = models.BooleanField(_('Office Hours Enabled'), default=True)
    office_hours = models.JSONField(_('Office Hours'), default=dict, blank=True)
    offline_message = models.TextField(_('Offline Message'), blank=True)
    
    # Legal Disclaimers
    legal_disclaimer = models.TextField(
        _('Legal Disclaimer'), 
        default=_('This chat provides general legal information only and does not constitute legal advice.')
    )
    show_disclaimer = models.BooleanField(_('Show Disclaimer'), default=True)
    
    # Analytics
    track_analytics = models.BooleanField(_('Track Analytics'), default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Chat Configuration')
        verbose_name_plural = _('Chat Configurations')
    
    def __str__(self):
        return f"{self.lawyer.full_name} - Chat Config"
    
    def get_welcome_message(self, language='ru'):
        """Get welcome message for specific language"""
        welcome_messages = {
            'ru': self.welcome_message_ru,
            'ky': self.welcome_message_ky,
            'en': self.welcome_message_en,
        }
        
        return welcome_messages.get(language, self.welcome_message_ru) or self.get_default_welcome_message(language)
    
    def get_default_welcome_message(self, language='ru'):
        """Get default welcome message"""
        messages = {
            'ru': f"Здравствуйте! Я помощник юриста {self.lawyer.full_name}. Как могу помочь?",
            'ky': f"Саламатсызбы! Мен юрист {self.lawyer.full_name}дын жардамчысымын. Кантип жардам бере алам?",
            'en': f"Hello! I'm {self.lawyer.full_name}'s legal assistant. How can I help you?",
        }
        return messages.get(language, messages['ru'])
    
    def is_office_hours(self):
        """Check if current time is within office hours"""
        if not self.office_hours_enabled or not self.office_hours:
            return True
        
        from django.utils import timezone
        now = timezone.now()
        weekday = now.strftime('%A').lower()
        current_time = now.time()
        
        office_schedule = self.office_hours.get(weekday)
        if not office_schedule or not office_schedule.get('enabled', False):
            return False
        
        from datetime import time
        start_time = time.fromisoformat(office_schedule.get('start', '09:00'))
        end_time = time.fromisoformat(office_schedule.get('end', '18:00'))
        
        return start_time <= current_time <= end_time


class ChatFeedback(models.Model):
    """Feedback and ratings for chat interactions"""
    RATING_CHOICES = [
        (1, _('Poor')),
        (2, _('Fair')),
        (3, _('Good')),
        (4, _('Very Good')),
        (5, _('Excellent')),
    ]
    
    session = models.OneToOneField(ChatSession, on_delete=models.CASCADE, related_name='feedback')
    rating = models.PositiveSmallIntegerField(_('Rating'), choices=RATING_CHOICES)
    comment = models.TextField(_('Comment'), blank=True)
    would_recommend = models.BooleanField(_('Would Recommend'), default=True)
    
    # Specific feedback areas
    helpfulness = models.PositiveSmallIntegerField(_('Helpfulness'), choices=RATING_CHOICES, blank=True, null=True)
    response_quality = models.PositiveSmallIntegerField(_('Response Quality'), choices=RATING_CHOICES, blank=True, null=True)
    ease_of_use = models.PositiveSmallIntegerField(_('Ease of Use'), choices=RATING_CHOICES, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Chat Feedback')
        verbose_name_plural = _('Chat Feedback')
    
    def __str__(self):
        return f"{self.session} - Rating: {self.rating}/5"


class ChatAnalytics(models.Model):
    """Daily chat analytics for lawyers"""
    lawyer = models.ForeignKey('lawyers.Lawyer', on_delete=models.CASCADE, related_name='chat_analytics')
    date = models.DateField(_('Date'))
    
    # Session Statistics
    total_sessions = models.PositiveIntegerField(_('Total Sessions'), default=0)
    completed_sessions = models.PositiveIntegerField(_('Completed Sessions'), default=0)
    abandoned_sessions = models.PositiveIntegerField(_('Abandoned Sessions'), default=0)
    
    # Message Statistics
    total_messages = models.PositiveIntegerField(_('Total Messages'), default=0)
    avg_messages_per_session = models.FloatField(_('Avg Messages per Session'), default=0)
    avg_response_time_ms = models.PositiveIntegerField(_('Avg Response Time (ms)'), default=0)
    
    # Lead Generation
    leads_generated = models.PositiveIntegerField(_('Leads Generated'), default=0)
    consultation_requests = models.PositiveIntegerField(_('Consultation Requests'), default=0)
    conversion_rate = models.FloatField(_('Conversion Rate'), default=0)
    
    # User Satisfaction
    avg_rating = models.FloatField(_('Average Rating'), default=0)
    total_feedback = models.PositiveIntegerField(_('Total Feedback'), default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Chat Analytics')
        verbose_name_plural = _('Chat Analytics')
        unique_together = ['lawyer', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.lawyer.full_name} - {self.date}"
