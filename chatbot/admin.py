from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import ChatSession, ChatMessage, ChatConfiguration, ChatFeedback, ChatAnalytics


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['visitor_display', 'lawyer', 'status', 'language', 'is_lead_display', 'started_at']
    list_filter = ['status', 'language', 'consultation_requested', 'started_at']
    search_fields = ['visitor_name', 'visitor_email', 'visitor_phone', 'lawyer__user__username']
    readonly_fields = ['session_id', 'started_at', 'last_activity', 'duration']
    
    fieldsets = (
        (_('Session Information'), {
            'fields': ('lawyer', 'session_id', 'status', 'language')
        }),
        (_('Visitor Information'), {
            'fields': ('visitor_name', 'visitor_email', 'visitor_phone', 'visitor_ip')
        }),
        (_('Case Information'), {
            'fields': ('legal_category', 'consultation_requested', 'consultation_message', 'preferred_contact_method')
        }),
        (_('Technical Details'), {
            'fields': ('user_agent', 'referrer'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('started_at', 'ended_at', 'last_activity'),
            'classes': ('collapse',)
        }),
    )
    
    def visitor_display(self, obj):
        if obj.visitor_name:
            return obj.visitor_name
        elif obj.visitor_email:
            return obj.visitor_email
        elif obj.visitor_ip:
            return f"Anonymous ({obj.visitor_ip})"
        return "Unknown Visitor"
    visitor_display.short_description = _('Visitor')
    
    def is_lead_display(self, obj):
        return obj.is_lead
    is_lead_display.boolean = True
    is_lead_display.short_description = _('Is Lead')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session_visitor', 'message_type', 'content_preview', 'response_time_ms', 'created_at']
    list_filter = ['message_type', 'ai_model', 'is_helpful', 'needs_review', 'created_at']
    search_fields = ['session__visitor_name', 'content']
    readonly_fields = ['created_at']
    
    fieldsets = (
        (_('Message Information'), {
            'fields': ('session', 'message_type', 'content')
        }),
        (_('AI Metadata'), {
            'fields': ('ai_model', 'response_time_ms', 'tokens_used'),
            'classes': ('collapse',)
        }),
        (_('Quality Control'), {
            'fields': ('is_helpful', 'needs_review')
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def session_visitor(self, obj):
        return obj.session.visitor_name or f"Session {obj.session.id}"
    session_visitor.short_description = _('Session')
    
    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = _('Content')


@admin.register(ChatConfiguration)
class ChatConfigurationAdmin(admin.ModelAdmin):
    list_display = ['lawyer', 'ai_model', 'collect_contact_info', 'office_hours_enabled', 'updated_at']
    list_filter = ['ai_model', 'collect_contact_info', 'office_hours_enabled', 'show_disclaimer']
    search_fields = ['lawyer__user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('Basic Configuration'), {
            'fields': ('lawyer', 'ai_model', 'system_prompt')
        }),
        (_('AI Settings'), {
            'fields': ('max_tokens', 'temperature', 'response_delay_seconds')
        }),
        (_('Chat Behavior'), {
            'fields': ('collect_contact_info', 'auto_suggest_consultation')
        }),
        (_('Welcome Messages'), {
            'fields': ('welcome_message_ru', 'welcome_message_ky', 'welcome_message_en')
        }),
        (_('Business Hours'), {
            'fields': ('office_hours_enabled', 'office_hours', 'offline_message')
        }),
        (_('Legal & Compliance'), {
            'fields': ('legal_disclaimer', 'show_disclaimer')
        }),
        (_('Analytics'), {
            'fields': ('track_analytics',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ChatFeedback)
class ChatFeedbackAdmin(admin.ModelAdmin):
    list_display = ['session_visitor', 'rating', 'would_recommend', 'created_at']
    list_filter = ['rating', 'would_recommend', 'helpfulness', 'response_quality', 'ease_of_use']
    search_fields = ['session__visitor_name', 'comment']
    readonly_fields = ['created_at']
    
    fieldsets = (
        (_('Feedback'), {
            'fields': ('session', 'rating', 'comment', 'would_recommend')
        }),
        (_('Detailed Ratings'), {
            'fields': ('helpfulness', 'response_quality', 'ease_of_use')
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def session_visitor(self, obj):
        return obj.session.visitor_name or f"Session {obj.session.id}"
    session_visitor.short_description = _('Session')


@admin.register(ChatAnalytics)
class ChatAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['lawyer', 'date', 'total_sessions', 'leads_generated', 'avg_rating', 'conversion_rate']
    list_filter = ['date', 'lawyer']
    search_fields = ['lawyer__user__username']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        (_('Analytics Data'), {
            'fields': ('lawyer', 'date')
        }),
        (_('Session Statistics'), {
            'fields': ('total_sessions', 'completed_sessions', 'abandoned_sessions')
        }),
        (_('Message Statistics'), {
            'fields': ('total_messages', 'avg_messages_per_session', 'avg_response_time_ms')
        }),
        (_('Lead Generation'), {
            'fields': ('leads_generated', 'consultation_requests', 'conversion_rate')
        }),
        (_('User Satisfaction'), {
            'fields': ('avg_rating', 'total_feedback')
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# Inline admin for related models
class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    fields = ['message_type', 'content', 'response_time_ms', 'created_at']
    readonly_fields = ['created_at']
    show_change_link = True


# Add inlines to ChatSession admin
ChatSessionAdmin.inlines = [ChatMessageInline]
