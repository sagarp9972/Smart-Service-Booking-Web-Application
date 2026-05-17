from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

@admin.register(CustomUser)
class CUAdmin(UserAdmin):
    list_display=['username','email','first_name','role','is_active']
    list_filter=['role','is_active']
    fieldsets=UserAdmin.fieldsets+(('Profile',{'fields':('role','phone','address','profile_pic','bio','dark_mode')}),)

@admin.register(Category)
class CatAdmin(admin.ModelAdmin):
    list_display=['name','emoji','icon','order','online_only']
    list_editable=['online_only']

@admin.register(ServiceProvider)
class ProvAdmin(admin.ModelAdmin):
    list_display=['full_name','category','phone','experience_years','availability','verified']
    list_filter=['category','availability','verified']
    list_editable=['verified','availability']
    search_fields=['full_name','phone','specialization']

@admin.register(Service)
class SvcAdmin(admin.ModelAdmin):
    list_display=['name','category','provider','price','duration_minutes','available']
    list_filter=['category','available']
    list_editable=['available']

@admin.register(Booking)
class BkAdmin(admin.ModelAdmin):
    list_display=['id','user','service','date','status','payment_method','payment_status','total_price']
    list_filter=['status','payment_method','payment_status']
    list_editable=['status','payment_status']

@admin.register(Review)
class RevAdmin(admin.ModelAdmin):
    list_display=['user','service','provider','rating','created_at']

admin.site.register(Notification)
admin.site.register(Favorite)
admin.site.register(TimeSlot)
admin.site.register(Message)
