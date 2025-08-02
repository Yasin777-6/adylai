from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Subscription, LawFirm, Lawyer


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['plan_type', 'status', 'starts_at', 'expires_at', 'created_at']
    list_filter = ['plan_type', 'status', 'created_at']
    search_fields = ['plan_type']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Plan Information', {
            'fields': ('plan_type', 'status')
        }),
        ('Dates', {
            'fields': ('starts_at', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def subscription_status(self, obj):
        return obj.is_active
    subscription_status.boolean = True
    subscription_status.short_description = 'Active'


@admin.register(LawFirm)
class LawFirmAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'created_at']
    search_fields = ['name', 'address']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'address', 'description')
        }),
        ('Branding', {
            'fields': ('logo',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class LawyerInline(admin.StackedInline):
    model = Lawyer
    can_delete = False
    verbose_name_plural = 'Lawyer Profile'
    fields = ['bio', 'photo', 'license_number', 'years_experience', 'consultation_fee', 'website_published']
    readonly_fields = ['domain_slug', 'created_at', 'updated_at']


@admin.register(Lawyer)
class LawyerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'years_experience', 'website_published', 'subscription_status', 'created_at']
    list_filter = ['website_published', 'primary_language', 'website_theme', 'years_experience', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'license_number', 'domain_slug']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at', 'domain_slug']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'firm', 'subscription')
        }),
        ('Professional Information', {
            'fields': ('bio', 'photo', 'license_number', 'years_experience', 'consultation_fee', 'specialties')
        }),
        ('Website Settings', {
            'fields': ('website_theme', 'primary_language', 'domain_slug', 'website_published')
        }),
        ('Office Hours', {
            'fields': ('office_hours',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    full_name.short_description = 'Full Name'
    full_name.admin_order_field = 'user__first_name'
    
    def email(self, obj):
        return obj.user.email
    email.short_description = 'Email'
    email.admin_order_field = 'user__email'
    
    def subscription_status(self, obj):
        if obj.subscription:
            return obj.subscription.is_active
        return False
    subscription_status.boolean = True
    subscription_status.short_description = 'Active Subscription'
    
    def website_url(self, obj):
        if obj.website_published:
            return f"/{obj.domain_slug}/"
        return "Not published"
    website_url.short_description = 'Website URL'
    
    actions = ['publish_websites', 'unpublish_websites']
    
    def publish_websites(self, request, queryset):
        for lawyer in queryset:
            lawyer.publish_website()
        self.message_user(request, f"Published websites for {queryset.count()} lawyers.")
    publish_websites.short_description = "Publish selected lawyers' websites"
    
    def unpublish_websites(self, request, queryset):
        for lawyer in queryset:
            lawyer.unpublish_website()
        self.message_user(request, f"Unpublished websites for {queryset.count()} lawyers.")
    unpublish_websites.short_description = "Unpublish selected lawyers' websites"


# Extend the User admin to include lawyer profile
class UserAdmin(BaseUserAdmin):
    inlines = (LawyerInline,)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
