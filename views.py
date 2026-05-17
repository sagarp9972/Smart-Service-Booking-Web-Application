from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg, Sum
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from functools import wraps
import datetime, uuid

from .models import (CustomUser, Category, Service, Booking, Review,
                     Notification, Favorite, TimeSlot, ServiceProvider, Message)
from .forms  import (RegisterForm, LoginForm, ProfileEditForm,
                     CustomPasswordChangeForm, ReviewForm, ServiceForm,
                     ServiceProviderForm, MessageForm, PaymentConfirmForm)

def admin_required(fn):
    @wraps(fn)
    def wrap(req,*a,**kw):
        if not req.user.is_authenticated: return redirect('login')
        if req.user.role!='admin': messages.error(req,'Admin access only.'); return redirect('home')
        return fn(req,*a,**kw)
    return wrap

def notif(user,title,msg,t='system'):
    Notification.objects.create(user=user,title=title,message=msg,type=t)

def make_slots(service,date_str):
    """Generate 30-min slots 9AM-6PM, skip slots in the past for today."""
    date=datetime.datetime.strptime(date_str,'%Y-%m-%d').date()
    now=datetime.datetime.now()
    cur=datetime.datetime.combine(date,datetime.time(9,0))
    end=datetime.datetime.combine(date,datetime.time(18,0))
    slots=[]
    while cur<end:
        nxt=cur+datetime.timedelta(minutes=30)
        # Skip past slots for today
        if date==now.date() and cur<=now:
            cur=nxt; continue
        s,_=TimeSlot.objects.get_or_create(
            service=service,date=date,start_time=cur.time(),
            defaults={'end_time':nxt.time()})
        slots.append(s); cur=nxt
    return slots

def home(request):
    cats=Category.objects.annotate(sc=Count('services')).filter(sc__gt=0).order_by('order','name')
    featured=Service.objects.filter(available=True).annotate(ar=Avg('reviews__rating')).order_by('-ar')[:6]
    trending=Service.objects.filter(available=True).annotate(bc=Count('bookings')).order_by('-bc')[:4]
    return render(request,'core/home.html',{
        'categories':cats,'featured_services':featured,'trending_services':trending,
        'total_services':Service.objects.filter(available=True).count(),
        'total_bookings':Booking.objects.count(),
        'total_users':CustomUser.objects.filter(role='user').count(),
    })

def register_view(request):
    if request.user.is_authenticated: return redirect('home')
    form=RegisterForm(request.POST or None,request.FILES or None)
    if request.method=='POST' and form.is_valid():
        user=form.save()
        if request.FILES.get('profile_pic'):
            user.profile_pic=request.FILES['profile_pic']; user.save()
        notif(user,'Welcome to SmartService!',f'Hi {user.first_name}, your account is ready.')
        messages.success(request,'Account created! Please login.')
        return redirect('login')
    return render(request,'core/register.html',{'form':form})

def login_view(request):
    if request.user.is_authenticated: return redirect('home')
    form=LoginForm(request,data=request.POST or None)
    if request.method=='POST' and form.is_valid():
        u=form.get_user(); login(request,u)
        messages.success(request,f'Welcome back, {u.first_name or u.username}!')
        return redirect('home')
    return render(request,'core/login.html',{'form':form})

def logout_view(request):
    logout(request); messages.info(request,'Logged out.'); return redirect('login')

@login_required
def profile_view(request):
    bks=Booking.objects.filter(user=request.user)
    favs=Favorite.objects.filter(user=request.user).select_related('service')
    revs=Review.objects.filter(user=request.user).select_related('service')
    stats={k:bks.filter(status=k).count() if k!='total' else bks.count()
           for k in ['total','pending','confirmed','completed','cancelled']}
    return render(request,'core/profile.html',{
        'bookings':bks.order_by('-created_at')[:5],
        'favorites':favs,'reviews':revs,'stats':stats})

@login_required
def edit_profile(request):
    form=ProfileEditForm(request.POST or None,request.FILES or None,instance=request.user)
    if form.is_valid(): form.save(); messages.success(request,'Profile updated!'); return redirect('profile')
    return render(request,'core/edit_profile.html',{'form':form})

@login_required
def change_password(request):
    form=CustomPasswordChangeForm(request.user,request.POST or None)
    if form.is_valid():
        update_session_auth_hash(request,form.save())
        messages.success(request,'Password changed!'); return redirect('profile')
    return render(request,'core/change_password.html',{'form':form})

def services_view(request):
    q=request.GET.get('q','').strip(); cat=request.GET.get('category','').strip()
    mn=request.GET.get('price_min',''); mx=request.GET.get('price_max',''); srt=request.GET.get('sort','')
    cats=Category.objects.annotate(sc=Count('services')).filter(sc__gt=0).prefetch_related('services')
    svcs=Service.objects.filter(available=True).select_related('category','provider')
    if q:   svcs=svcs.filter(Q(name__icontains=q)|Q(description__icontains=q)|Q(category__name__icontains=q)|Q(specialization__icontains=q))
    if cat: svcs=svcs.filter(category__id=cat)
    if mn:  svcs=svcs.filter(price__gte=mn)
    if mx:  svcs=svcs.filter(price__lte=mx)
    if srt=='price_low':    svcs=svcs.order_by('price')
    elif srt=='price_high': svcs=svcs.order_by('-price')
    elif srt=='rating':     svcs=svcs.annotate(ar=Avg('reviews__rating')).order_by('-ar')
    elif srt=='popular':    svcs=svcs.annotate(bc=Count('bookings')).order_by('-bc')
    return render(request,'core/services.html',{
        'services':svcs,'categories':cats,'query':q,
        'selected_category':cat,'price_min':mn,'price_max':mx,'sort_by':srt})

def service_detail(request,pk):
    svc=get_object_or_404(Service,pk=pk,available=True)
    revs=Review.objects.filter(service=svc).select_related('user').order_by('-created_at')
    rel=Service.objects.filter(category=svc.category,available=True).exclude(pk=pk)[:4]
    is_fav=Favorite.objects.filter(user=request.user,service=svc).exists() if request.user.is_authenticated else False
    today=timezone.now().date()
    for i in range(7): make_slots(svc,(today+datetime.timedelta(days=i)).strftime('%Y-%m-%d'))
    # Check if user has a completed booking eligible for review
    can_review=False
    if request.user.is_authenticated:
        has_completed=Booking.objects.filter(user=request.user,service=svc,status='completed').exists()
        already_reviewed=Review.objects.filter(user=request.user,service=svc).exists()
        can_review=has_completed and not already_reviewed
    return render(request,'core/service_detail.html',{
        'service':svc,'reviews':revs,'related':rel,'is_fav':is_fav,
        'review_form':ReviewForm(),'can_review':can_review})

def provider_detail(request,pk):
    provider=get_object_or_404(ServiceProvider,pk=pk)
    services=Service.objects.filter(provider=provider,available=True)
    reviews=Review.objects.filter(provider=provider).select_related('user','service').order_by('-created_at')
    bookings_count=Booking.objects.filter(provider=provider,status='completed').count()
    return render(request,'core/provider_detail.html',{
        'provider':provider,'services':services,
        'reviews':reviews,'bookings_count':bookings_count})

def get_slots(request,service_id):
    date_str=request.GET.get('date','')
    if not date_str: return JsonResponse({'slots':[]})
    svc=get_object_or_404(Service,pk=service_id)
    slots=make_slots(svc,date_str)
    data=[{'id':s.id,'time':s.start_time.strftime('%I:%M %p'),'available':s.is_available} for s in slots]
    return JsonResponse({'slots':data})

@login_required
def booking_view(request,service_id):
    svc=get_object_or_404(Service,pk=service_id,available=True)
    today=timezone.now().date()
    for i in range(7): make_slots(svc,(today+datetime.timedelta(days=i)).strftime('%Y-%m-%d'))
    # Determine allowed payment methods for this category
    online_only=svc.category.online_only
    if request.method=='POST':
        date_str=request.POST.get('date','').strip()
        slot_id=request.POST.get('slot_id','').strip()
        notes=request.POST.get('notes','').strip()
        payment=request.POST.get('payment_method','cash')
        is_emergency=request.POST.get('is_emergency','')=='on'
        if not date_str:
            messages.error(request,'Please select a date.')
            return render(request,'core/booking.html',{'service':svc,'today':today.strftime('%Y-%m-%d'),'online_only':online_only})
        if not slot_id:
            messages.error(request,'Please select a time slot.')
            return render(request,'core/booking.html',{
                'service':svc,'today':today.strftime('%Y-%m-%d'),
                'selected_date':date_str,'online_only':online_only})
        try: sl=TimeSlot.objects.get(pk=slot_id,service=svc)
        except TimeSlot.DoesNotExist:
            messages.error(request,'Invalid slot.'); return redirect('booking',service_id=service_id)
        if not sl.is_available:
            messages.error(request,'Slot already booked. Choose another.')
            return render(request,'core/booking.html',{
                'service':svc,'today':today.strftime('%Y-%m-%d'),
                'selected_date':date_str,'online_only':online_only})
        valid_pays=['cash','upi','gpay','phonepe','paytm','card']
        if payment not in valid_pays: payment='upi'
        if online_only and payment=='cash': payment='upi'
        bk=Booking(); bk.user=request.user; bk.service=svc
        bk.provider=svc.provider; bk.date=sl.date; bk.time=sl.start_time
        bk.time_slot=sl; bk.total_price=svc.price; bk.notes=notes
        bk.payment_method=payment; bk.discount_amt=0; bk.is_emergency=is_emergency
        if payment=='cash':
            bk.status='confirmed'; bk.payment_status='pending'; bk.save()
            sl.current_bookings+=1; sl.save()
            notif(bk.user,'Booking Confirmed!',f'{svc.name} on {bk.date} at {bk.time} confirmed. Pay cash on service.','booking')
            messages.success(request,f'Booking confirmed for {svc.name}!')
            return redirect('booking_detail',booking_id=bk.pk)
        else:
            bk.status='pending'; bk.payment_status='pending'; bk.save()
            sl.current_bookings+=1; sl.save()
            return redirect('payment_page',booking_id=bk.pk)
    return render(request,'core/booking.html',{
        'service':svc,'today':today.strftime('%Y-%m-%d'),'online_only':online_only})

@login_required
def payment_page(request,booking_id):
    bk=get_object_or_404(Booking,pk=booking_id,user=request.user)
    upi_id=getattr(settings,'UPI_ID','smartservice@upi')
    upi_name=getattr(settings,'UPI_NAME','SmartService')
    amount=float(bk.get_final_price())
    pay_note=f"SmartService Booking #{bk.pk}"
    gpay_link=f"tez://upi/pay?pa={upi_id}&pn={upi_name}&am={amount}&tn={pay_note}"
    phonepe_link=f"phonepe://pay?pa={upi_id}&pn={upi_name}&am={amount}&tn={pay_note}"
    paytm_link=f"paytmmp://pay?pa={upi_id}&pn={upi_name}&am={amount}&tn={pay_note}"
    upi_base=f"upi://pay?pa={upi_id}&pn={upi_name}&am={amount}&tn={pay_note}"
    if request.method=='POST':
        form=PaymentConfirmForm(request.POST)
        if form.is_valid():
            txn=form.cleaned_data.get('transaction_id','').strip()
            bk.transaction_id=txn or str(uuid.uuid4())[:12].upper()
            bk.payment_status='paid'; bk.status='confirmed'; bk.save()
            notif(bk.user,'Payment Confirmed!',f'Payment of ₹{amount} for {bk.service.name} booking #{bk.pk} confirmed.','payment')
            messages.success(request,f'Payment confirmed! Booking #{bk.pk} is confirmed.')
            return redirect('booking_detail',booking_id=bk.pk)
    else: form=PaymentConfirmForm()
    return render(request,'core/payment_page.html',{
        'booking':bk,'form':form,'amount':amount,'upi_id':upi_id,
        'gpay_link':gpay_link,'phonepe_link':phonepe_link,
        'paytm_link':paytm_link,'upi_base':upi_base,'pay_note':pay_note})

@login_required
def booking_history(request):
    sf=request.GET.get('status','')
    bks=Booking.objects.filter(user=request.user)
    if sf: bks=bks.filter(status=sf)
    all_=Booking.objects.filter(user=request.user)
    stats={k:all_.filter(status=k).count() if k!='total' else all_.count()
           for k in ['total','pending','confirmed','completed','cancelled']}
    return render(request,'core/booking_history.html',
        {'bookings':bks.order_by('-created_at'),'stats':stats,'status_filter':sf})

@login_required
def booking_detail(request,booking_id):
    bk=get_object_or_404(Booking,pk=booking_id,user=request.user)
    has_review=Review.objects.filter(user=request.user,service=bk.service).exists()
    msgs=Message.objects.filter(booking=bk).order_by('created_at')
    # Can review only if completed and not already reviewed
    can_review=bk.status=='completed' and not has_review
    return render(request,'core/booking_detail.html',{
        'booking':bk,'has_review':has_review,'can_review':can_review,
        'review_form':ReviewForm(),'messages_list':msgs,'msg_form':MessageForm()})

@login_required
def cancel_booking(request,booking_id):
    bk=get_object_or_404(Booking,pk=booking_id,user=request.user)
    if bk.status in ['pending','confirmed']:
        bk.status='cancelled'; bk.save()
        if bk.time_slot:
            bk.time_slot.current_bookings=max(0,bk.time_slot.current_bookings-1); bk.time_slot.save()
        notif(bk.user,'Booking Cancelled',f'Booking for {bk.service.name} has been cancelled.','booking')
        messages.success(request,'Booking cancelled.')
    return redirect('booking_history')

@login_required
def reschedule_booking(request,booking_id):
    bk=get_object_or_404(Booking,pk=booking_id,user=request.user)
    if bk.status not in ['pending','confirmed']:
        messages.error(request,'Cannot reschedule.'); return redirect('booking_detail',booking_id=booking_id)
    today=timezone.now().date()
    for i in range(7): make_slots(bk.service,(today+datetime.timedelta(days=i)).strftime('%Y-%m-%d'))
    if request.method=='POST':
        slot_id=request.POST.get('slot_id','').strip()
        if not slot_id:
            messages.error(request,'Select a time slot.'); return redirect('reschedule_booking',booking_id=booking_id)
        try: sl=TimeSlot.objects.get(pk=slot_id,service=bk.service)
        except TimeSlot.DoesNotExist:
            messages.error(request,'Invalid slot.'); return redirect('reschedule_booking',booking_id=booking_id)
        if not sl.is_available:
            messages.error(request,'Slot not available.'); return redirect('reschedule_booking',booking_id=booking_id)
        if bk.time_slot:
            bk.time_slot.current_bookings=max(0,bk.time_slot.current_bookings-1); bk.time_slot.save()
        bk.date=sl.date; bk.time=sl.start_time; bk.time_slot=sl; bk.status='rescheduled'; bk.save()
        sl.current_bookings+=1; sl.save()
        notif(bk.user,'Booking Rescheduled',f'{bk.service.name} rescheduled to {bk.date} at {bk.time}.','booking')
        messages.success(request,'Booking rescheduled!')
        return redirect('booking_detail',booking_id=bk.pk)
    return render(request,'core/reschedule.html',{'booking':bk,'today':today.strftime('%Y-%m-%d'),'service':bk.service})

@login_required
def add_review(request,service_id):
    svc=get_object_or_404(Service,pk=service_id)
    if request.method=='POST':
        rating=request.POST.get('rating','').strip()
        comment=request.POST.get('comment','').strip()
        if not rating or not rating.isdigit() or not (1<=int(rating)<=5):
            messages.error(request,'Please select a rating between 1 and 5 stars.')
            return redirect('service_detail',pk=service_id)
        has_bk=Booking.objects.filter(user=request.user,service=svc,status='completed').exists()
        if not has_bk:
            messages.error(request,'You can only review after a completed booking.')
            return redirect('service_detail',pk=service_id)
        rev,cr=Review.objects.get_or_create(user=request.user,service=svc,
            defaults={'rating':int(rating),'comment':comment,'provider':svc.provider})
        if not cr:
            rev.rating=int(rating); rev.comment=comment; rev.save()
        messages.success(request,'Review submitted successfully! Thank you.')
    return redirect('service_detail',pk=service_id)

@login_required
def toggle_favorite(request,service_id):
    svc=get_object_or_404(Service,pk=service_id)
    fv,cr=Favorite.objects.get_or_create(user=request.user,service=svc)
    if not cr: fv.delete(); messages.info(request,'Removed from favorites.')
    else: messages.success(request,f'{svc.name} added to favorites!')
    return redirect('service_detail',pk=service_id)

@login_required
def notifications_view(request):
    nts=Notification.objects.filter(user=request.user)
    nts.filter(is_read=False).update(is_read=True)
    return render(request,'core/notifications.html',{'notifications':nts})

def unread_count(request):
    if request.user.is_authenticated:
        return JsonResponse({'count':Notification.objects.filter(user=request.user,is_read=False).count()})
    return JsonResponse({'count':0})

@login_required
def send_message(request,booking_id):
    bk=get_object_or_404(Booking,pk=booking_id)
    if request.user!=bk.user and request.user.role!='admin':
        messages.error(request,'Not allowed.'); return redirect('home')
    if request.method=='POST':
        form=MessageForm(request.POST)
        if form.is_valid(): Message.objects.create(booking=bk,sender=request.user,content=form.cleaned_data['content'])
    return redirect('booking_detail',booking_id=booking_id)

# ── ADMIN ────────────────────────────────────
@admin_required
def dashboard_view(request):
    ctx={
        'total_users':   CustomUser.objects.filter(role='user').count(),
        'total_services':Service.objects.count(),
        'total_bookings':Booking.objects.count(),
        'pending_count': Booking.objects.filter(status='pending').count(),
        'total_revenue': Booking.objects.filter(status='completed').aggregate(t=Sum('total_price'))['t'] or 0,
        'paid_revenue':  Booking.objects.filter(payment_status='paid').aggregate(t=Sum('total_price'))['t'] or 0,
        'recent_bookings':Booking.objects.order_by('-created_at')[:10],
        'bookings_by_status':{s:Booking.objects.filter(status=s).count() for s,_ in Booking.STATUS},
        'top_services':  Service.objects.annotate(bc=Count('bookings')).order_by('-bc')[:5],
        'providers':     ServiceProvider.objects.count(),
    }
    return render(request,'core/dashboard.html',ctx)

@admin_required
def admin_services(request):
    return render(request,'core/admin_services.html',
        {'services':Service.objects.all().select_related('category','provider').order_by('-created_at')})

@admin_required
def admin_add_service(request):
    form=ServiceForm(request.POST or None,request.FILES or None)
    if form.is_valid(): form.save(); messages.success(request,'Service added!'); return redirect('admin_services')
    return render(request,'core/admin_service_form.html',{'form':form,'title':'Add Service'})

@admin_required
def admin_edit_service(request,pk):
    svc=get_object_or_404(Service,pk=pk)
    form=ServiceForm(request.POST or None,request.FILES or None,instance=svc)
    if form.is_valid(): form.save(); messages.success(request,'Updated!'); return redirect('admin_services')
    return render(request,'core/admin_service_form.html',{'form':form,'title':'Edit Service'})

@admin_required
def admin_delete_service(request,pk):
    svc=get_object_or_404(Service,pk=pk)
    if request.method=='POST': svc.delete(); messages.success(request,'Deleted!'); return redirect('admin_services')
    return render(request,'core/admin_confirm_delete.html',{'object':svc,'type':'Service'})

@admin_required
def admin_bookings(request):
    sf=request.GET.get('status','')
    bks=Booking.objects.all().order_by('-created_at')
    if sf: bks=bks.filter(status=sf)
    return render(request,'core/admin_bookings.html',{'bookings':bks,'status_filter':sf})

@admin_required
def admin_update_booking(request,pk):
    bk=get_object_or_404(Booking,pk=pk)
    if request.method=='POST':
        ns=request.POST.get('status')
        if ns in dict(Booking.STATUS):
            bk.status=ns; bk.save()
            notif(bk.user,f'Booking {ns.title()}',f'Your {bk.service.name} booking is now {ns}.','booking')
    return redirect('admin_bookings')

@admin_required
def admin_users(request):
    users=CustomUser.objects.filter(role='user').annotate(bc=Count('bookings')).order_by('-date_joined')
    return render(request,'core/admin_users.html',{'users':users})

@admin_required
def admin_providers(request):
    providers=ServiceProvider.objects.all().select_related('category','user').order_by('-created_at')
    return render(request,'core/admin_providers.html',{'providers':providers})

@admin_required
def admin_add_provider(request):
    form=ServiceProviderForm(request.POST or None,request.FILES or None)
    if form.is_valid():
        prov=form.save(commit=False)
        uname=form.cleaned_data['full_name'].lower().replace(' ','_')[:20]
        u,_=CustomUser.objects.get_or_create(username=uname,defaults={
            'first_name':form.cleaned_data['full_name'].split()[0],
            'email':form.cleaned_data.get('email',''),'role':'provider'})
        prov.user=u; prov.verified=True; prov.save()
        messages.success(request,'Provider added!'); return redirect('admin_providers')
    return render(request,'core/admin_service_form.html',{'form':form,'title':'Add Provider'})

@admin_required
def admin_add_category(request):
    from django import forms as df
    class CatForm(df.ModelForm):
        class Meta:
            model=Category; fields=['name','icon','emoji','description','order','online_only']
            widgets={f:df.TextInput(attrs={'class':'form-control'}) for f in ['name','icon','emoji','description']}
            widgets['order']=df.NumberInput(attrs={'class':'form-control'})
    form=CatForm(request.POST or None)
    if form.is_valid(): form.save(); messages.success(request,'Category added!'); return redirect('admin_services')
    return render(request,'core/admin_service_form.html',{'form':form,'title':'Add Category'})
