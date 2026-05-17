from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import datetime

class CustomUser(AbstractUser):
    ROLE = (('user','User'),('admin','Admin'),('provider','Service Provider'))
    role        = models.CharField(max_length=10, choices=ROLE, default='user')
    phone       = models.CharField(max_length=15, blank=True, null=True)
    address     = models.TextField(blank=True, null=True)
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio         = models.TextField(blank=True, null=True)
    dark_mode   = models.BooleanField(default=False)
    def __str__(self): return f"{self.username} ({self.role})"

class Category(models.Model):
    name  = models.CharField(max_length=100, unique=True)
    icon  = models.CharField(max_length=60, default='fa-concierge-bell')
    emoji = models.CharField(max_length=10, default='🔧')
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    # online_only: True means no cash payment allowed
    online_only = models.BooleanField(default=False)
    class Meta:
        verbose_name_plural='Categories'
        ordering=['order','name']
    def __str__(self): return f"{self.emoji} {self.name}"

class ServiceProvider(models.Model):
    AVAIL = (('available','Available'),('busy','Busy'),('offline','Offline'))
    user             = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='provider_profile')
    category         = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='providers')
    full_name        = models.CharField(max_length=150)
    phone            = models.CharField(max_length=15)
    email            = models.EmailField(blank=True)
    profile_pic      = models.ImageField(upload_to='providers/', blank=True, null=True)
    experience_years = models.IntegerField(default=0)
    education        = models.CharField(max_length=300, blank=True)
    specialization   = models.CharField(max_length=200, blank=True)
    workplace_name   = models.CharField(max_length=200, blank=True)
    workplace_address= models.TextField(blank=True)
    workplace_lat    = models.FloatField(null=True, blank=True)
    workplace_lng    = models.FloatField(null=True, blank=True)
    about            = models.TextField(blank=True)
    availability     = models.CharField(max_length=15, choices=AVAIL, default='available')
    emergency_contact= models.CharField(max_length=15, blank=True)
    languages        = models.CharField(max_length=200, blank=True)
    verified         = models.BooleanField(default=False)
    created_at       = models.DateTimeField(auto_now_add=True)
    @property
    def avg_rating(self):
        r = self.ratings.all()
        return round(sum(x.rating for x in r)/r.count(),1) if r.exists() else 0
    @property
    def total_reviews(self): return self.ratings.count()
    def __str__(self): return f"{self.full_name}"

class Service(models.Model):
    PKG=(('basic','Basic'),('standard','Standard'),('premium','Premium'))
    name             = models.CharField(max_length=100)
    category         = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='services')
    provider         = models.ForeignKey(ServiceProvider, on_delete=models.SET_NULL, null=True, blank=True, related_name='services')
    description      = models.TextField()
    price            = models.DecimalField(max_digits=10, decimal_places=2)
    package_type     = models.CharField(max_length=10, choices=PKG, default='basic')
    duration_minutes = models.IntegerField(default=60)
    available        = models.BooleanField(default=True)
    image            = models.ImageField(upload_to='services/', blank=True, null=True)
    specialization   = models.CharField(max_length=100, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['name']
    @property
    def avg_rating(self):
        r = self.reviews.all()
        return round(sum(x.rating for x in r)/r.count(),1) if r.exists() else 0
    @property
    def review_count(self): return self.reviews.count()
    def __str__(self): return f"{self.name} — ₹{self.price}"

class TimeSlot(models.Model):
    service          = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='slots')
    date             = models.DateField()
    start_time       = models.TimeField()
    end_time         = models.TimeField()
    max_bookings     = models.IntegerField(default=1)
    current_bookings = models.IntegerField(default=0)
    class Meta:
        unique_together=['service','date','start_time']
        ordering=['date','start_time']
    @property
    def is_available(self): return self.current_bookings < self.max_bookings
    def __str__(self): return f"{self.service.name}|{self.date} {self.start_time}"

class Booking(models.Model):
    STATUS=(('pending','Pending'),('confirmed','Confirmed'),('in_progress','In Progress'),
            ('completed','Completed'),('cancelled','Cancelled'),('rescheduled','Rescheduled'))
    PAY=(('cash','Cash on Service'),('upi','UPI'),('gpay','Google Pay'),
         ('phonepe','PhonePe'),('paytm','Paytm'),('card','Card'))
    PAY_STATUS=(('pending','Payment Pending'),('paid','Paid'),('failed','Failed'),('refunded','Refunded'))
    user           = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bookings')
    service        = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='bookings')
    provider       = models.ForeignKey(ServiceProvider, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    time_slot      = models.ForeignKey(TimeSlot, on_delete=models.SET_NULL, null=True, blank=True)
    date           = models.DateField()
    time           = models.TimeField()
    status         = models.CharField(max_length=15, choices=STATUS, default='confirmed')
    notes          = models.TextField(blank=True, null=True)
    total_price    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=10, choices=PAY, default='cash')
    payment_status = models.CharField(max_length=10, choices=PAY_STATUS, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True)
    discount_amt   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_emergency   = models.BooleanField(default=False)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)
    class Meta: ordering=['-created_at']
    def save(self,*args,**kwargs):
        if not self.total_price: self.total_price=self.service.price
        super().save(*args,**kwargs)
    def get_final_price(self): return self.total_price - self.discount_amt
    def __str__(self): return f"#{self.pk} {self.user.username}→{self.service.name}"

class Review(models.Model):
    user       = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviews')
    service    = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='reviews')
    provider   = models.ForeignKey(ServiceProvider, on_delete=models.SET_NULL, null=True, blank=True, related_name='ratings')
    booking    = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review', null=True, blank=True)
    rating     = models.IntegerField(validators=[MinValueValidator(1),MaxValueValidator(5)])
    comment    = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: unique_together=['user','service']
    def __str__(self): return f"{self.user.username}→{self.service.name}:{self.rating}★"

class Notification(models.Model):
    TYPES=(('booking','Booking'),('payment','Payment'),('system','System'))
    user       = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    title      = models.CharField(max_length=200)
    message    = models.TextField()
    type       = models.CharField(max_length=10, choices=TYPES, default='system')
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['-created_at']

class Favorite(models.Model):
    user       = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='favorites')
    service    = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: unique_together=['user','service']

class Message(models.Model):
    booking    = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='messages')
    sender     = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    content    = models.TextField()
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['created_at']
