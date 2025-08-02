from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User


class Lead(models.Model):
    """Client leads generated from website or chatbot"""
    STATUS_CHOICES = [
        ('new', _('New')),
        ('contacted', _('Contacted')),
        ('qualified', _('Qualified')),
        ('converted', _('Converted')),
        ('lost', _('Lost')),
        ('spam', _('Spam')),
    ]
    
    PRIORITY_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('urgent', _('Urgent')),
    ]
    
    SOURCE_CHOICES = [
        ('website_form', _('Website Contact Form')),
        ('chatbot', _('AI Chatbot')),
        ('phone', _('Phone Call')),
        ('email', _('Email')),
        ('referral', _('Referral')),
        ('social_media', _('Social Media')),
        ('google_ads', _('Google Ads')),
        ('other', _('Other')),
    ]
    
    lawyer = models.ForeignKey('lawyers.Lawyer', on_delete=models.CASCADE, related_name='leads')
    
    # Contact Information
    name = models.CharField(_('Full Name'), max_length=200)
    email = models.EmailField(_('Email'), blank=True)
    phone = models.CharField(_('Phone'), max_length=20, blank=True)
    
    # Lead Details
    legal_category = models.CharField(_('Legal Category'), max_length=100, blank=True)
    case_description = models.TextField(_('Case Description'))
    estimated_budget = models.DecimalField(_('Estimated Budget'), max_digits=10, decimal_places=2, blank=True, null=True)
    urgency = models.CharField(_('Urgency'), max_length=20, default='medium')
    
    # Lead Management
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField(_('Priority'), max_length=20, choices=PRIORITY_CHOICES, default='medium')
    source = models.CharField(_('Source'), max_length=30, choices=SOURCE_CHOICES, default='website_form')
    
    # Tracking
    ip_address = models.GenericIPAddressField(_('IP Address'), blank=True, null=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    referrer_url = models.URLField(_('Referrer URL'), blank=True)
    utm_source = models.CharField(_('UTM Source'), max_length=100, blank=True)
    utm_medium = models.CharField(_('UTM Medium'), max_length=100, blank=True)
    utm_campaign = models.CharField(_('UTM Campaign'), max_length=100, blank=True)
    
    # Notes and Follow-up
    internal_notes = models.TextField(_('Internal Notes'), blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_leads')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    contacted_at = models.DateTimeField(_('First Contact Date'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Lead')
        verbose_name_plural = _('Leads')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.legal_category or 'General Inquiry'}"
    
    @property
    def contact_info(self):
        """Get primary contact information"""
        if self.phone and self.email:
            return f"{self.email} / {self.phone}"
        return self.email or self.phone or "No contact info"
    
    @property
    def days_since_created(self):
        """Calculate days since lead was created"""
        from django.utils import timezone
        return (timezone.now().date() - self.created_at.date()).days


class Consultation(models.Model):
    """Consultation appointments scheduled with lawyers"""
    STATUS_CHOICES = [
        ('scheduled', _('Scheduled')),
        ('confirmed', _('Confirmed')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('no_show', _('No Show')),
        ('rescheduled', _('Rescheduled')),
    ]
    
    TYPE_CHOICES = [
        ('free', _('Free Consultation')),
        ('paid', _('Paid Consultation')),
        ('follow_up', _('Follow-up')),
        ('emergency', _('Emergency')),
    ]
    
    DURATION_CHOICES = [
        (15, _('15 minutes')),
        (30, _('30 minutes')),
        (45, _('45 minutes')),
        (60, _('1 hour')),
        (90, _('1.5 hours')),
        (120, _('2 hours')),
    ]
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='consultations')
    lawyer = models.ForeignKey('lawyers.Lawyer', on_delete=models.CASCADE, related_name='consultations')
    
    # Appointment Details
    scheduled_time = models.DateTimeField(_('Scheduled Time'))
    duration_minutes = models.PositiveIntegerField(_('Duration (minutes)'), choices=DURATION_CHOICES, default=30)
    consultation_type = models.CharField(_('Type'), max_length=20, choices=TYPE_CHOICES, default='free')
    
    # Status and Management
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='scheduled')
    fee = models.DecimalField(_('Fee'), max_digits=10, decimal_places=2, default=0)
    
    # Meeting Details
    meeting_method = models.CharField(
        _('Meeting Method'), 
        max_length=20,
        choices=[
            ('in_person', _('In Person')),
            ('phone', _('Phone Call')),
            ('video', _('Video Call')),
            ('zoom', _('Zoom')),
        ],
        default='in_person'
    )
    meeting_link = models.URLField(_('Meeting Link'), blank=True)
    location = models.TextField(_('Location'), blank=True)
    
    # Consultation Content
    agenda = models.TextField(_('Agenda'), blank=True)
    client_questions = models.TextField(_('Client Questions'), blank=True)
    lawyer_notes = models.TextField(_('Lawyer Notes'), blank=True)
    outcome = models.TextField(_('Outcome'), blank=True)
    
    # Follow-up
    follow_up_required = models.BooleanField(_('Follow-up Required'), default=False)
    follow_up_date = models.DateField(_('Follow-up Date'), blank=True, null=True)
    follow_up_notes = models.TextField(_('Follow-up Notes'), blank=True)
    
    # Communication
    confirmation_sent = models.BooleanField(_('Confirmation Sent'), default=False)
    reminder_sent = models.BooleanField(_('Reminder Sent'), default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(_('Completed At'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Consultation')
        verbose_name_plural = _('Consultations')
        ordering = ['scheduled_time']
    
    def __str__(self):
        return f"{self.lead.name} - {self.scheduled_time.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def end_time(self):
        """Calculate consultation end time"""
        from datetime import timedelta
        return self.scheduled_time + timedelta(minutes=self.duration_minutes)
    
    @property
    def is_upcoming(self):
        """Check if consultation is upcoming"""
        from django.utils import timezone
        return self.scheduled_time > timezone.now() and self.status in ['scheduled', 'confirmed']
    
    @property
    def is_overdue(self):
        """Check if consultation is overdue"""
        from django.utils import timezone
        return self.scheduled_time < timezone.now() and self.status in ['scheduled', 'confirmed']


class LeadNote(models.Model):
    """Notes and communications with leads"""
    NOTE_TYPES = [
        ('call', _('Phone Call')),
        ('email', _('Email')),
        ('meeting', _('Meeting')),
        ('sms', _('SMS')),
        ('general', _('General Note')),
    ]
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lead_notes')
    
    note_type = models.CharField(_('Note Type'), max_length=20, choices=NOTE_TYPES, default='general')
    title = models.CharField(_('Title'), max_length=200, blank=True)
    content = models.TextField(_('Content'))
    
    # Communication tracking
    is_client_communication = models.BooleanField(_('Client Communication'), default=False)
    communication_successful = models.BooleanField(_('Communication Successful'), default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Lead Note')
        verbose_name_plural = _('Lead Notes')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.lead.name} - {self.note_type}: {self.content[:50]}..."


class LeadSource(models.Model):
    """Track and manage lead sources for analytics"""
    lawyer = models.ForeignKey('lawyers.Lawyer', on_delete=models.CASCADE, related_name='lead_sources')
    name = models.CharField(_('Source Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    
    # Tracking
    is_active = models.BooleanField(_('Is Active'), default=True)
    cost_per_lead = models.DecimalField(_('Cost per Lead'), max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Lead Source')
        verbose_name_plural = _('Lead Sources')
        unique_together = ['lawyer', 'name']
    
    def __str__(self):
        return f"{self.lawyer.full_name} - {self.name}"
    
    def get_leads_count(self):
        """Get total leads from this source"""
        return Lead.objects.filter(lawyer=self.lawyer, source=self.name).count()
    
    def get_conversion_rate(self):
        """Calculate conversion rate for this source"""
        total_leads = self.get_leads_count()
        if total_leads == 0:
            return 0
        
        converted_leads = Lead.objects.filter(
            lawyer=self.lawyer, 
            source=self.name, 
            status='converted'
        ).count()
        
        return (converted_leads / total_leads) * 100


class LeadAnalytics(models.Model):
    """Daily lead analytics for lawyers"""
    lawyer = models.ForeignKey('lawyers.Lawyer', on_delete=models.CASCADE, related_name='lead_analytics')
    date = models.DateField(_('Date'))
    
    # Lead Statistics
    new_leads = models.PositiveIntegerField(_('New Leads'), default=0)
    total_leads = models.PositiveIntegerField(_('Total Leads'), default=0)
    qualified_leads = models.PositiveIntegerField(_('Qualified Leads'), default=0)
    converted_leads = models.PositiveIntegerField(_('Converted Leads'), default=0)
    lost_leads = models.PositiveIntegerField(_('Lost Leads'), default=0)
    
    # Consultation Statistics
    consultations_scheduled = models.PositiveIntegerField(_('Consultations Scheduled'), default=0)
    consultations_completed = models.PositiveIntegerField(_('Consultations Completed'), default=0)
    consultations_cancelled = models.PositiveIntegerField(_('Consultations Cancelled'), default=0)
    
    # Conversion Metrics
    lead_to_consultation_rate = models.FloatField(_('Lead to Consultation Rate'), default=0)
    consultation_to_client_rate = models.FloatField(_('Consultation to Client Rate'), default=0)
    
    # Source Analysis
    top_lead_sources = models.JSONField(_('Top Lead Sources'), default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Lead Analytics')
        verbose_name_plural = _('Lead Analytics')
        unique_together = ['lawyer', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.lawyer.full_name} - {self.date}"
