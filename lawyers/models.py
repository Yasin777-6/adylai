from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver


class Subscription(models.Model):
    """Subscription plans for lawyers"""
    PLAN_CHOICES = [
        ('basic', _('Basic - $50/month')),
        ('pro', _('Pro - $150/month')),
        ('premium', _('Premium - $300/month')),
    ]
    
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('cancelled', _('Cancelled')),
        ('expired', _('Expired')),
        ('trial', _('Trial')),
    ]
    
    plan_type = models.CharField(_('Plan Type'), max_length=20, choices=PLAN_CHOICES, default='basic')
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='trial')
    starts_at = models.DateTimeField(_('Starts At'))
    expires_at = models.DateTimeField(_('Expires At'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Subscription')
        verbose_name_plural = _('Subscriptions')
    
    def __str__(self):
        return f"{self.plan_type} - {self.status}"
    
    @property
    def is_active(self):
        return self.status == 'active'


class LawFirm(models.Model):
    """Law firm information (optional for lawyers)"""
    name = models.CharField(_('Firm Name'), max_length=200)
    address = models.TextField(_('Address'))
    description = models.TextField(_('Description'), blank=True)
    logo = models.ImageField(
        _('Logo'), 
        upload_to='firm_logos/', 
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Law Firm')
        verbose_name_plural = _('Law Firms')
    
    def __str__(self):
        return self.name


class Lawyer(models.Model):
    """Extended user profile for lawyers"""
    SPECIALTY_CHOICES = [
        ('civil', _('Civil Law')),
        ('criminal', _('Criminal Law')),
        ('business', _('Business Law')),
        ('family', _('Family Law')),
        ('divorce', _('Divorce')),
        ('real_estate', _('Real Estate')),
        ('labor', _('Labor Law')),
        ('tax', _('Tax Law')),
        ('bankruptcy', _('Bankruptcy')),
        ('immigration', _('Immigration')),
        ('personal_injury', _('Personal Injury')),
        ('intellectual_property', _('Intellectual Property')),
    ]
    
    THEME_CHOICES = [
        ('blue', _('Professional Blue')),
        ('navy', _('Navy Corporate')),
        ('gray', _('Modern Gray')),
        ('dark', _('Dark Professional')),
    ]
    
    LANGUAGE_CHOICES = [
        ('ru', _('Russian')),
        ('ky', _('Kyrgyz')),
        ('en', _('English')),
    ]
    
    # Core Information
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lawyer_profile')
    firm = models.ForeignKey(LawFirm, on_delete=models.SET_NULL, null=True, blank=True)
    subscription = models.OneToOneField(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Contact Information (simplified - no phone/email since AI chat handles contact)
    bio = models.TextField(_('Biography'), blank=True)
    photo = models.ImageField(
        _('Photo'), 
        upload_to='lawyer_photos/', 
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    
    # Professional Information
    specialties = models.JSONField(_('Specialties'), default=list, help_text=_('List of legal specialties'))
    license_number = models.CharField(_('License Number'), max_length=50, blank=True)
    years_experience = models.PositiveIntegerField(_('Years of Experience'), default=0)
    consultation_fee = models.DecimalField(_('Consultation Fee'), max_digits=10, decimal_places=2, default=0)
    
    # Website Settings
    website_theme = models.CharField(_('Website Theme'), max_length=20, choices=THEME_CHOICES, default='blue')
    primary_language = models.CharField(_('Primary Language'), max_length=5, choices=LANGUAGE_CHOICES, default='ru')
    domain_slug = models.SlugField(_('Website URL'), unique=True, max_length=100)
    website_published = models.BooleanField(_('Website Published'), default=False)
    
    # Office Hours
    office_hours = models.JSONField(_('Office Hours'), default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Lawyer')
        verbose_name_plural = _('Lawyers')
    
    def __str__(self):
        return self.user.get_full_name() or self.user.username
    
    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username
    
    @property
    def email(self):
        return self.user.email
    
    @property
    def website_url(self):
        """Public website URL"""
        if self.website_published:
            return f"/{self.domain_slug}/"
        return None
    
    def save(self, *args, **kwargs):
        if not self.domain_slug:
            # Auto-generate domain slug from name
            base_slug = slugify(self.user.get_full_name() or self.user.username)
            if not base_slug:
                base_slug = f"lawyer-{self.user.pk}"
            
            # Ensure uniqueness
            original_slug = base_slug
            counter = 1
            while Lawyer.objects.filter(domain_slug=base_slug).exclude(pk=self.pk).exists():
                base_slug = f"{original_slug}-{counter}"
                counter += 1
            
            self.domain_slug = base_slug
        
        super().save(*args, **kwargs)
    
    def publish_website(self):
        """Publish the lawyer's website to make AI chatbot active"""
        self.website_published = True
        self.save()
        
        # Create or update website record
        from website_builder.models import Website
        website, created = Website.objects.get_or_create(
            lawyer=self,
            defaults={
                'title': f"{self.full_name} - Legal Services",
                'domain_slug': self.domain_slug,
                'is_published': True,
                'status': 'published'
            }
        )
        if not created:
            website.is_published = True
            website.status = 'published'
            website.save()
        
        return website
    
    def unpublish_website(self):
        """Unpublish the website and disable AI chatbot"""
        self.website_published = False
        self.save()
        
        # Update website record
        try:
            from website_builder.models import Website
            website = Website.objects.get(lawyer=self)
            website.is_published = False
            website.status = 'draft'
            website.save()
        except Website.DoesNotExist:
            pass


@receiver(post_save, sender=User)
def create_lawyer_profile(sender, instance, created, **kwargs):
    """Automatically create lawyer profile when user is created"""
    if created:
        Lawyer.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_lawyer_profile(sender, instance, **kwargs):
    """Save lawyer profile when user is saved"""
    if hasattr(instance, 'lawyer_profile'):
        instance.lawyer_profile.save()
