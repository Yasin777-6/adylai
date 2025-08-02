from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
import json


class WebsiteTemplate(models.Model):
    """Pre-built website templates"""
    name = models.CharField(_('Template Name'), max_length=100)
    description = models.TextField(_('Description'))
    thumbnail = models.ImageField(
        _('Template Thumbnail'), 
        upload_to='template_thumbnails/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    template_data = models.JSONField(_('Template Data'), default=dict)
    specialties = models.JSONField(_('Suitable Specialties'), default=list, blank=True)
    is_premium = models.BooleanField(_('Premium Template'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Website Template')
        verbose_name_plural = _('Website Templates')
    
    def __str__(self):
        return self.name


class Website(models.Model):
    """Lawyer's website configuration and content"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('published', _('Published')),
        ('archived', _('Archived')),
    ]
    
    lawyer = models.OneToOneField('lawyers.Lawyer', on_delete=models.CASCADE, related_name='website')
    template = models.ForeignKey(WebsiteTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Website Settings
    title = models.CharField(_('Website Title'), max_length=200)
    meta_description = models.TextField(_('Meta Description'), max_length=160, blank=True)
    domain_slug = models.SlugField(_('Domain Slug'), unique=True, max_length=100)
    custom_domain = models.CharField(_('Custom Domain'), max_length=100, blank=True)
    
    # Status and Publishing
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='draft')
    is_published = models.BooleanField(_('Is Published'), default=False)
    
    # Content
    content_data = models.JSONField(_('Content Data'), default=dict)
    
    # SEO and Analytics
    google_analytics_id = models.CharField(_('Google Analytics ID'), max_length=50, blank=True)
    facebook_pixel_id = models.CharField(_('Facebook Pixel ID'), max_length=50, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = _('Website')
        verbose_name_plural = _('Websites')
    
    def __str__(self):
        return f"{self.lawyer.full_name}'s Website"
    
    @property
    def public_url(self):
        if self.custom_domain:
            return f"https://{self.custom_domain}"
        return f"/{self.domain_slug}/"
    
    def get_page_content(self, page_name):
        """Get content for a specific page"""
        return self.content_data.get('pages', {}).get(page_name, {})
    
    def set_page_content(self, page_name, content):
        """Set content for a specific page"""
        if 'pages' not in self.content_data:
            self.content_data['pages'] = {}
        self.content_data['pages'][page_name] = content
        self.save()


class WebsitePage(models.Model):
    """Individual pages within a website"""
    PAGE_TYPES = [
        ('home', _('Home')),
        ('about', _('About')),
        ('services', _('Services')),
        ('contact', _('Contact')),
        ('blog', _('Blog')),
        ('privacy', _('Privacy Policy')),
        ('terms', _('Terms of Service')),
        ('custom', _('Custom Page')),
    ]
    
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='pages')
    page_type = models.CharField(_('Page Type'), max_length=20, choices=PAGE_TYPES)
    title = models.CharField(_('Page Title'), max_length=200)
    slug = models.SlugField(_('Page Slug'), max_length=100)
    content = models.JSONField(_('Page Content'), default=dict)
    meta_description = models.TextField(_('Meta Description'), max_length=160, blank=True)
    is_published = models.BooleanField(_('Is Published'), default=True)
    order = models.PositiveIntegerField(_('Display Order'), default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Website Page')
        verbose_name_plural = _('Website Pages')
        unique_together = ['website', 'slug']
        ordering = ['order', 'title']
    
    def __str__(self):
        return f"{self.website.title} - {self.title}"
    
    @property
    def url(self):
        if self.page_type == 'home':
            return self.website.public_url
        return f"{self.website.public_url}{self.slug}/"


class WebsiteAsset(models.Model):
    """Images and documents uploaded for websites"""
    ASSET_TYPES = [
        ('image', _('Image')),
        ('document', _('Document')),
        ('logo', _('Logo')),
        ('favicon', _('Favicon')),
    ]
    
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='assets')
    asset_type = models.CharField(_('Asset Type'), max_length=20, choices=ASSET_TYPES)
    name = models.CharField(_('Asset Name'), max_length=200)
    file = models.FileField(
        _('File'), 
        upload_to='website_assets/',
        validators=[FileExtensionValidator(allowed_extensions=[
            'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg',  # Images
            'pdf', 'doc', 'docx', 'txt'  # Documents
        ])]
    )
    alt_text = models.CharField(_('Alt Text'), max_length=200, blank=True)
    description = models.TextField(_('Description'), blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Website Asset')
        verbose_name_plural = _('Website Assets')
    
    def __str__(self):
        return f"{self.website.title} - {self.name}"
    
    @property
    def is_image(self):
        return self.asset_type in ['image', 'logo', 'favicon']
    
    @property
    def file_extension(self):
        return self.file.name.split('.')[-1].lower() if self.file else None


class WebsiteAnalytics(models.Model):
    """Website analytics and visitor tracking"""
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField(_('Date'))
    page_views = models.PositiveIntegerField(_('Page Views'), default=0)
    unique_visitors = models.PositiveIntegerField(_('Unique Visitors'), default=0)
    bounce_rate = models.DecimalField(_('Bounce Rate'), max_digits=5, decimal_places=2, default=0)
    avg_session_duration = models.DurationField(_('Average Session Duration'), null=True, blank=True)
    
    # Top pages
    popular_pages = models.JSONField(_('Popular Pages'), default=list, blank=True)
    
    # Traffic sources
    traffic_sources = models.JSONField(_('Traffic Sources'), default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Website Analytics')
        verbose_name_plural = _('Website Analytics')
        unique_together = ['website', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.website.title} - {self.date}"
