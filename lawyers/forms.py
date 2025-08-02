from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Lawyer, LawFirm


class LawyerRegistrationForm(UserCreationForm):
    """Extended registration form for lawyers"""
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your first name'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your last name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email address'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Create a strong password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm your password'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class LawyerProfileForm(forms.ModelForm):
    """Form for editing lawyer profile - simplified since contact is handled by AI chat"""
    
    class Meta:
        model = Lawyer
        fields = [
            'bio', 'photo', 'specialties', 'license_number', 
            'years_experience', 'consultation_fee', 'website_theme', 
            'primary_language'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell potential clients about your experience and approach'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your bar license number'}),
            'years_experience': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'consultation_fee': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'Fee in KGS (0 for free)'}),
            'website_theme': forms.Select(attrs={'class': 'form-select'}),
            'primary_language': forms.Select(attrs={'class': 'form-select'}),
        }


class ContactForm(forms.Form):
    """Contact form for public websites - used when AI chat is not available"""
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your full name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your email address'})
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your phone number'})
    )
    legal_category = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Type of legal issue'})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your legal question or issue'})
    ) 