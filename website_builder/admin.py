from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import WebsiteTemplate, Website, WebsitePage, WebsiteAsset, WebsiteAnalytics


@admin.register(WebsiteTemplate)
class WebsiteTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_premium', 'created_at']
    list_filter = ['is_premium', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('Template Information'), {
            'fields': ('name', 'description', 'thumbnail', 'is_premium')
        }),
        (_('Configuration'), {
            'fields': ('specialties', 'template_data')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    list_display = ['title', 'lawyer', 'status', 'is_published', 'public_url_link', 'updated_at']
    list_filter = ['status', 'is_published', 'created_at']
    search_fields = ['title', 'lawyer__user__username', 'domain_slug']
    readonly_fields = ['created_at', 'updated_at', 'published_at', 'public_url']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('lawyer', 'template', 'title', 'meta_description')
        }),
        (_('Domain & Publishing'), {
            'fields': ('domain_slug', 'custom_domain', 'status', 'is_published', 'published_at')
        }),
        (_('Content'), {
            'fields': ('content_data',),
            'classes': ('collapse',)
        }),
        (_('Analytics & SEO'), {
            'fields': ('google_analytics_id', 'facebook_pixel_id')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def public_url_link(self, obj):
        if obj.is_published:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.public_url, obj.public_url)
        return _('Not published')
    public_url_link.short_description = _('Public URL')


@admin.register(WebsitePage)
class WebsitePageAdmin(admin.ModelAdmin):
    list_display = ['title', 'website', 'page_type', 'is_published', 'order', 'updated_at']
    list_filter = ['page_type', 'is_published', 'created_at']
    search_fields = ['title', 'website__title', 'slug']
    readonly_fields = ['created_at', 'updated_at', 'url']
    
    fieldsets = (
        (_('Page Information'), {
            'fields': ('website', 'page_type', 'title', 'slug', 'order')
        }),
        (_('Content'), {
            'fields': ('content',)
        }),
        (_('SEO'), {
            'fields': ('meta_description', 'is_published')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WebsiteAsset)
class WebsiteAssetAdmin(admin.ModelAdmin):
    list_display = ['name', 'website', 'asset_type', 'file_extension_display', 'created_at']
    list_filter = ['asset_type', 'created_at']
    search_fields = ['name', 'website__title']
    readonly_fields = ['created_at', 'updated_at', 'file_extension']
    
    fieldsets = (
        (_('Asset Information'), {
            'fields': ('website', 'asset_type', 'name', 'file')
        }),
        (_('Metadata'), {
            'fields': ('alt_text', 'description')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def file_extension_display(self, obj):
        return obj.file_extension or _('Unknown')
    file_extension_display.short_description = _('File Type')


@admin.register(WebsiteAnalytics)
class WebsiteAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['website', 'date', 'page_views', 'unique_visitors', 'bounce_rate']
    list_filter = ['date', 'website']
    search_fields = ['website__title']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        (_('Analytics Data'), {
            'fields': ('website', 'date')
        }),
        (_('Visitor Statistics'), {
            'fields': ('page_views', 'unique_visitors', 'bounce_rate', 'avg_session_duration')
        }),
        (_('Traffic Analysis'), {
            'fields': ('popular_pages', 'traffic_sources')
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# Inline admin for related models
class WebsitePageInline(admin.TabularInline):
    model = WebsitePage
    extra = 0
    fields = ['page_type', 'title', 'slug', 'is_published', 'order']
    readonly_fields = ['created_at']


class WebsiteAssetInline(admin.TabularInline):
    model = WebsiteAsset
    extra = 0
    fields = ['asset_type', 'name', 'file', 'alt_text']
    readonly_fields = ['created_at']


# Add inlines to Website admin
WebsiteAdmin.inlines = [WebsitePageInline, WebsiteAssetInline]
