from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from .models import CustomUser, Booking, Service, Review, ServiceProvider

class RegisterForm(UserCreationForm):
    email       = forms.EmailField(required=True)
    first_name  = forms.CharField(max_length=50)
    last_name   = forms.CharField(max_length=50)
    phone       = forms.CharField(max_length=15, required=False)
    profile_pic = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class':'form-control','accept':'image/*'}))
    class Meta:
        model  = CustomUser
        fields = ['username','first_name','last_name','email','phone','profile_pic','password1','password2']
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for f in self.fields:
            if f != 'profile_pic': self.fields[f].widget.attrs.update({'class':'form-control'})

class LoginForm(AuthenticationForm):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['username'].widget.attrs.update({'class':'form-control','placeholder':'Username'})
        self.fields['password'].widget.attrs.update({'class':'form-control','placeholder':'Password'})

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model  = CustomUser
        fields = ['first_name','last_name','email','phone','address','profile_pic','bio','dark_mode']
        widgets = {
            'first_name':  forms.TextInput(attrs={'class':'form-control'}),
            'last_name':   forms.TextInput(attrs={'class':'form-control'}),
            'email':       forms.EmailInput(attrs={'class':'form-control'}),
            'phone':       forms.TextInput(attrs={'class':'form-control'}),
            'address':     forms.Textarea(attrs={'class':'form-control','rows':2}),
            'bio':         forms.Textarea(attrs={'class':'form-control','rows':2}),
            'profile_pic': forms.FileInput(attrs={'class':'form-control'}),
        }

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for f in self.fields: self.fields[f].widget.attrs['class']='form-control'

class ReviewForm(forms.ModelForm):
    rating  = forms.IntegerField(min_value=1, max_value=5, widget=forms.HiddenInput())
    comment = forms.CharField(required=False, widget=forms.Textarea(
        attrs={'class':'form-control','rows':3,'placeholder':'Share your experience...'}))
    class Meta:
        model  = Review
        fields = ['rating','comment']

class ServiceForm(forms.ModelForm):
    class Meta:
        model  = Service
        fields = ['name','category','provider','description','price','package_type','duration_minutes','available','image','specialization']
        widgets = {
            'name':             forms.TextInput(attrs={'class':'form-control'}),
            'category':         forms.Select(attrs={'class':'form-select'}),
            'provider':         forms.Select(attrs={'class':'form-select'}),
            'description':      forms.Textarea(attrs={'class':'form-control','rows':3}),
            'price':            forms.NumberInput(attrs={'class':'form-control'}),
            'package_type':     forms.Select(attrs={'class':'form-select'}),
            'duration_minutes': forms.NumberInput(attrs={'class':'form-control'}),
            'specialization':   forms.TextInput(attrs={'class':'form-control'}),
            'image':            forms.FileInput(attrs={'class':'form-control'}),
        }

class ServiceProviderForm(forms.ModelForm):
    class Meta:
        model  = ServiceProvider
        fields = ['full_name','phone','email','category','profile_pic','experience_years',
                  'education','specialization','workplace_name','workplace_address',
                  'workplace_lat','workplace_lng','about','availability','emergency_contact','languages']
        widgets = {
            'full_name':       forms.TextInput(attrs={'class':'form-control'}),
            'phone':           forms.TextInput(attrs={'class':'form-control'}),
            'email':           forms.EmailInput(attrs={'class':'form-control'}),
            'category':        forms.Select(attrs={'class':'form-select'}),
            'availability':    forms.Select(attrs={'class':'form-select'}),
            'experience_years':forms.NumberInput(attrs={'class':'form-control'}),
            'education':       forms.TextInput(attrs={'class':'form-control'}),
            'specialization':  forms.TextInput(attrs={'class':'form-control'}),
            'workplace_name':  forms.TextInput(attrs={'class':'form-control'}),
            'workplace_address':forms.Textarea(attrs={'class':'form-control','rows':2}),
            'workplace_lat':   forms.NumberInput(attrs={'class':'form-control','step':'any'}),
            'workplace_lng':   forms.NumberInput(attrs={'class':'form-control','step':'any'}),
            'about':           forms.Textarea(attrs={'class':'form-control','rows':3}),
            'emergency_contact':forms.TextInput(attrs={'class':'form-control'}),
            'languages':       forms.TextInput(attrs={'class':'form-control'}),
            'profile_pic':     forms.FileInput(attrs={'class':'form-control'}),
        }

class MessageForm(forms.Form):
    content = forms.CharField(widget=forms.TextInput(attrs={
        'class':'form-control','placeholder':'Type your message...','autocomplete':'off'}))

class PaymentConfirmForm(forms.Form):
    transaction_id = forms.CharField(max_length=100, required=False,
        widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Enter UPI Transaction ID / Reference No.'}))
