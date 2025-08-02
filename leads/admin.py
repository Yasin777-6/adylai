from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Lead, Consultation, LeadNote, LeadSource, LeadAnalytics


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['name', 'lawyer', 'status', 'priority', 'source', 'contact_info_display', 'days_since_created_display', 'created_at']
    list_filter = ['status', 'priority', 'source', 'legal_category', 'created_at']
    search_fields = ['name', 'email', 'phone', 'case_description', 'lawyer__user__username']
    readonly_fields = ['created_at', 'updated_at', 'days_since_created']
    
    fieldsets = (
        (_('Lead Information'), {
            'fields': ('lawyer', 'name', 'email', 'phone')
        }),
        (_('Case Details'), {
            'fields': ('legal_category', 'case_description', 'estimated_budget', 'urgency')
        }),
        (_('Lead Management'), {
            'fields': ('status', 'priority', 'source', 'assigned_to')
        }),
        (_('Tracking Information'), {
            'fields': ('ip_address', 'user_agent', 'referrer_url'),
            'classes': ('collapse',)
        }),
        (_('Marketing Attribution'), {
            'fields': ('utm_source', 'utm_medium', 'utm_campaign'),
            'classes': ('collapse',)
        }),
        (_('Notes'), {
            'fields': ('internal_notes',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'contacted_at'),
            'classes': ('collapse',)
        }),
    )
    
    def contact_info_display(self, obj):
        return obj.contact_info
    contact_info_display.short_description = _('Contact Info')
    
    def days_since_created_display(self, obj):
        days = obj.days_since_created
        if days == 0:
            return _('Today')
        elif days == 1:
            return _('1 day ago')
        else:
            return f"{days} {_('days ago')}"
    days_since_created_display.short_description = _('Age')


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ['lead_name', 'lawyer', 'scheduled_time', 'duration_minutes', 'status', 'consultation_type', 'fee']
    list_filter = ['status', 'consultation_type', 'meeting_method', 'scheduled_time']
    search_fields = ['lead__name', 'lawyer__user__username', 'agenda']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'end_time']
    
    fieldsets = (
        (_('Consultation Information'), {
            'fields': ('lead', 'lawyer', 'consultation_type', 'fee')
        }),
        (_('Scheduling'), {
            'fields': ('scheduled_time', 'duration_minutes', 'status')
        }),
        (_('Meeting Details'), {
            'fields': ('meeting_method', 'meeting_link', 'location')
        }),
        (_('Content'), {
            'fields': ('agenda', 'client_questions', 'lawyer_notes', 'outcome')
        }),
        (_('Follow-up'), {
            'fields': ('follow_up_required', 'follow_up_date', 'follow_up_notes')
        }),
        (_('Communication'), {
            'fields': ('confirmation_sent', 'reminder_sent')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def lead_name(self, obj):
        return obj.lead.name
    lead_name.short_description = _('Client')


@admin.register(LeadNote)
class LeadNoteAdmin(admin.ModelAdmin):
    list_display = ['lead_name', 'note_type', 'title', 'author', 'is_client_communication', 'created_at']
    list_filter = ['note_type', 'is_client_communication', 'communication_successful', 'created_at']
    search_fields = ['lead__name', 'title', 'content', 'author__username']
    readonly_fields = ['created_at']
    
    fieldsets = (
        (_('Note Information'), {
            'fields': ('lead', 'author', 'note_type', 'title')
        }),
        (_('Content'), {
            'fields': ('content',)
        }),
        (_('Communication Tracking'), {
            'fields': ('is_client_communication', 'communication_successful')
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def lead_name(self, obj):
        return obj.lead.name
    lead_name.short_description = _('Lead')


@admin.register(LeadSource)
class LeadSourceAdmin(admin.ModelAdmin):
    list_display = ['lawyer', 'name', 'is_active', 'cost_per_lead', 'leads_count_display', 'conversion_rate_display']
    list_filter = ['is_active', 'created_at']
    search_fields = ['lawyer__user__username', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('Source Information'), {
            'fields': ('lawyer', 'name', 'description', 'is_active')
        }),
        (_('Tracking'), {
            'fields': ('cost_per_lead',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def leads_count_display(self, obj):
        return obj.get_leads_count()
    leads_count_display.short_description = _('Total Leads')
    
    def conversion_rate_display(self, obj):
        rate = obj.get_conversion_rate()
        return f"{rate:.1f}%" if rate else "0%"
    conversion_rate_display.short_description = _('Conversion Rate')


@admin.register(LeadAnalytics)
class LeadAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['lawyer', 'date', 'new_leads', 'qualified_leads', 'converted_leads', 'lead_to_consultation_rate', 'consultation_to_client_rate']
    list_filter = ['date', 'lawyer']
    search_fields = ['lawyer__user__username']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        (_('Analytics Data'), {
            'fields': ('lawyer', 'date')
        }),
        (_('Lead Statistics'), {
            'fields': ('new_leads', 'total_leads', 'qualified_leads', 'converted_leads', 'lost_leads')
        }),
        (_('Consultation Statistics'), {
            'fields': ('consultations_scheduled', 'consultations_completed', 'consultations_cancelled')
        }),
        (_('Conversion Metrics'), {
            'fields': ('lead_to_consultation_rate', 'consultation_to_client_rate')
        }),
        (_('Source Analysis'), {
            'fields': ('top_lead_sources',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# Inline admin for related models
class LeadNoteInline(admin.TabularInline):
    model = LeadNote
    extra = 0
    fields = ['note_type', 'title', 'content', 'is_client_communication', 'created_at']
    readonly_fields = ['created_at']


class ConsultationInline(admin.StackedInline):
    model = Consultation
    extra = 0
    fields = ['scheduled_time', 'duration_minutes', 'status', 'consultation_type', 'meeting_method']
    readonly_fields = ['created_at']


# Add inlines to Lead admin
LeadAdmin.inlines = [LeadNoteInline, ConsultationInline]
