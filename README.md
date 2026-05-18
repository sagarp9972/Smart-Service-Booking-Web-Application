# 🛠️ SmartService — Service Booking Web Application

A full-stack Django web application for booking home, health, and professional services online. Built as an internship project.

---

## 📋 Project Overview

SmartService is a complete service booking platform where users can:
- Browse and search 67+ services across 8 categories
- View service provider details (name, phone, education, experience, hospital/workplace)
- Book appointments with time slots (9AM–6PM, every 30 minutes)
- Pay via Cash, Google Pay, PhonePe, Paytm, UPI, or Card
- Track booking status (Pending → Confirmed → In Progress → Completed)
- Rate and review completed services
- Chat with service provider
- Reschedule or cancel bookings

---

## 🗂️ Project Structure

```
smart_service/                  ← Django project root
├── manage.py                   ← Django management script
├── db.sqlite3                  ← SQLite database (pre-seeded)
├── seed.py                     ← Data seeding script
├── requirements.txt            ← Python dependencies
├── media/                      ← Uploaded images (profiles, services)
├── smart_service/
│   ├── settings.py             ← Project settings
│   ├── urls.py                 ← Root URL configuration
│   ├── wsgi.py
│   └── asgi.py
└── core/                       ← Main application
    ├── models.py               ← Database models
    ├── views.py                ← Business logic / page controllers
    ├── urls.py                 ← App URL patterns
    ├── forms.py                ← Django forms
    ├── admin.py                ← Django admin configuration
    ├── apps.py
    ├── migrations/             ← Database migrations
    ├── templates/core/         ← HTML templates (18 pages)
    │   ├── base.html           ← Master layout (navbar, footer)
    │   ├── home.html           ← Homepage with search & categories
    │   ├── services.html       ← All services with filter/search
    │   ├── service_detail.html ← Service details + reviews
    │   ├── provider_detail.html← Provider profile + map
    │   ├── booking.html        ← Booking form with time slots
    │   ├── payment_page.html   ← UPI payment (GPay/PhonePe/Paytm)
    │   ├── booking_history.html← User booking dashboard
    │   ├── booking_detail.html ← Booking details + chat + review
    │   ├── reschedule.html     ← Reschedule booking
    │   ├── profile.html        ← User profile page
    │   ├── edit_profile.html   ← Edit profile
    │   ├── change_password.html
    │   ├── register.html       ← Registration with profile photo
    │   ├── login.html
    │   ├── notifications.html
    │   ├── dashboard.html      ← Admin dashboard
    │   ├── admin_services.html
    │   ├── admin_bookings.html
    │   ├── admin_providers.html
    │   └── admin_users.html
    └── static/core/
        ├── css/style.css       ← Custom styles (dark theme support)
        └── js/main.js          ← JavaScript (slots, star rating, etc.)
```

---

## 🗃️ Database Models

### CustomUser
| Field | Type | Description |
|---|---|---|
| username | CharField | Unique login name |
| first_name, last_name | CharField | Full name |
| email | EmailField | Email address |
| phone | CharField | Mobile number |
| profile_pic | ImageField | Optional profile photo |
| role | CharField | user / admin / provider |
| address | TextField | Home address |
| bio | TextField | Short bio |
| dark_mode | BooleanField | UI theme preference |

### Category
| Field | Type | Description |
|---|---|---|
| name | CharField | Doctor, Mechanic, Tutor, etc. |
| icon | CharField | Font Awesome icon class |
| emoji | CharField | Category emoji (🏥, 🚗, 🎓...) |
| order | IntegerField | Display order |
| online_only | BooleanField | If True, cash payment not allowed (Tutor) |

### ServiceProvider
| Field | Type | Description |
|---|---|---|
| full_name | CharField | Provider's full name |
| phone | CharField | Contact number |
| email | EmailField | Email |
| category | ForeignKey | Linked category |
| experience_years | IntegerField | Years of experience |
| education | CharField | Qualification / degree |
| specialization | CharField | Area of expertise |
| workplace_name | CharField | Hospital / shop / clinic name |
| workplace_address | TextField | Full address |
| workplace_lat / lng | FloatField | GPS coordinates for Google Maps |
| about | TextField | Bio / description |
| availability | CharField | available / busy / offline |
| emergency_contact | CharField | Emergency phone (for doctors) |
| languages | CharField | Languages spoken |
| verified | BooleanField | Admin verification badge |

### Service
| Field | Type | Description |
|---|---|---|
| name | CharField | Service name |
| category | ForeignKey | Linked category |
| provider | ForeignKey | Assigned service provider |
| description | TextField | Service description |
| price | DecimalField | Price in INR |
| duration_minutes | IntegerField | Service duration |
| available | BooleanField | Active/inactive |
| image | ImageField | Service photo |
| specialization | CharField | e.g. "Cardiologist", "Brake Specialist" |

### TimeSlot
| Field | Type | Description |
|---|---|---|
| service | ForeignKey | Linked service |
| date | DateField | Slot date |
| start_time | TimeField | Slot start (9:00 AM) |
| end_time | TimeField | Slot end (9:30 AM) |
| max_bookings | IntegerField | Max bookings per slot |
| current_bookings | IntegerField | Current booking count |

### Booking
| Field | Type | Description |
|---|---|---|
| user | ForeignKey | Who booked |
| service | ForeignKey | Which service |
| provider | ForeignKey | Assigned provider |
| time_slot | ForeignKey | Selected time slot |
| date | DateField | Appointment date |
| time | TimeField | Appointment time |
| status | CharField | pending/confirmed/in_progress/completed/cancelled/rescheduled |
| payment_method | CharField | cash/upi/gpay/phonepe/paytm/card |
| payment_status | CharField | pending/paid/failed/refunded |
| transaction_id | CharField | UPI transaction reference |
| total_price | DecimalField | Total amount |
| discount_amt | DecimalField | Discount applied |
| notes | TextField | Special requests |
| is_emergency | BooleanField | Emergency flag (Doctor) |

### Review
| Field | Type | Description |
|---|---|---|
| user | ForeignKey | Reviewer |
| service | ForeignKey | Reviewed service |
| provider | ForeignKey | Reviewed provider |
| booking | OneToOneField | Linked completed booking |
| rating | IntegerField | 1 to 5 stars |
| comment | TextField | Written review |

### Notification
| Field | Type | Description |
|---|---|---|
| user | ForeignKey | Recipient |
| title | CharField | Notification title |
| message | TextField | Notification body |
| type | CharField | booking / payment / system |
| is_read | BooleanField | Read status |

### Message
| Field | Type | Description |
|---|---|---|
| booking | ForeignKey | Linked booking |
| sender | ForeignKey | Message sender |
| content | TextField | Message text |
| is_read | BooleanField | Read status |

### Favorite
| Field | Type | Description |
|---|---|---|
| user | ForeignKey | User who favorited |
| service | ForeignKey | Favorited service |

---

## 🔗 URL Patterns

| URL | View | Description |
|---|---|---|
| `/` | home | Homepage |
| `/register/` | register_view | User registration |
| `/login/` | login_view | User login |
| `/logout/` | logout_view | Logout |
| `/profile/` | profile_view | User profile |
| `/profile/edit/` | edit_profile | Edit profile |
| `/profile/password/` | change_password | Change password |
| `/services/` | services_view | All services with search/filter |
| `/services/<pk>/` | service_detail | Service detail + reviews |
| `/services/<id>/slots/` | get_slots | AJAX: load time slots |
| `/provider/<pk>/` | provider_detail | Provider profile + map |
| `/book/<service_id>/` | booking_view | Booking form |
| `/payment/<booking_id>/` | payment_page | UPI payment page |
| `/my-bookings/` | booking_history | My bookings dashboard |
| `/my-bookings/<id>/` | booking_detail | Booking detail + chat |
| `/cancel/<id>/` | cancel_booking | Cancel booking |
| `/reschedule/<id>/` | reschedule_booking | Reschedule booking |
| `/review/<service_id>/` | add_review | Submit review |
| `/favorite/<service_id>/` | toggle_favorite | Add/remove favorite |
| `/notifications/` | notifications_view | Notifications |
| `/notifications/count/` | unread_count | AJAX: unread count |
| `/message/<booking_id>/` | send_message | Send chat message |
| `/dashboard/` | dashboard_view | Admin dashboard |
| `/dashboard/services/` | admin_services | Manage services |
| `/dashboard/bookings/` | admin_bookings | Manage bookings |
| `/dashboard/providers/` | admin_providers | Manage providers |
| `/dashboard/users/` | admin_users | Manage users |
| `/dashboard/category/add/` | admin_add_category | Add category |

---

## ⚙️ Settings

| Setting | Value | Description |
|---|---|---|
| DEBUG | True | Development mode |
| DATABASE | SQLite3 | db.sqlite3 |
| AUTH_USER_MODEL | core.CustomUser | Custom user model |
| TIME_ZONE | Asia/Kolkata | IST timezone |
| MEDIA_ROOT | /media/ | Uploaded files |
| UPI_ID | smartservice@upi | Your UPI ID for payments |
| UPI_NAME | SmartService | Your UPI display name |

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10+
- pip

### Steps

**1. Extract the ZIP**
```bash
unzip Smart-Service-Booking-Web-Application.zip
cd Smart-Service-Booking-Web-Application
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Database is already set up**
The `db.sqlite3` file is included with all data pre-loaded.

**4. Run the server**
```bash
python manage.py runserver
```

**5. Open browser**
```
http://127.0.0.1:8000
```

---

## 🔑 Login Credentials

| Role | Username | Password | Access |
|---|---|---|---|
| Admin | `admin` | `admin123` | Full admin dashboard |
| User | `sagar` | `sagar123` | Book services, profile |

### Admin Panel
```
http://127.0.0.1:8000/admin/
Username: admin
Password: admin123
```

### Admin Dashboard
```
http://127.0.0.1:8000/dashboard/
```

---

## 📦 Seed Data Included

| Item | Count |
|---|---|
| Categories | 8 |
| Services | 67 |
| Service Providers | 67 (one per service) |
| Users | 2 (admin + sagar) |

### Categories
| # | Category | Services | Notes |
|---|---|---|---|
| 1 | 🏥 Doctor | 22 | All specialties |
| 2 | 🚗 Mechanic | 8 | All vehicle services |
| 3 | 🎓 Tutor | 8 | Online payment only |
| 4 | 🔧 Plumber | 6 | |
| 5 | ⚡ Electrician | 6 | |
| 6 | 🧹 Cleaner | 6 | |
| 7 | 🪚 Carpenter | 5 | |
| 8 | ✂️ Salon | 6 | |

### Re-seed database (if needed)
```bash
python manage.py shell < seed.py
# OR
python seed.py
```

---

## 💳 Payment Flow

```
User selects service
       ↓
Chooses date + time slot
       ↓
Selects payment method
       ↓
     Cash?          UPI / GPay / PhonePe / Paytm / Card?
       ↓                          ↓
  Booking confirmed          Payment page
  immediately                    ↓
                          Open app (GPay/PhonePe/Paytm)
                                 ↓
                         Enter Transaction ID
                                 ↓
                          Booking confirmed
```

---

## ⏰ Time Slot System

Slots are generated automatically from **9:00 AM to 6:00 PM** every **30 minutes**:

| Group | Slots |
|---|---|
| ☀️ Morning | 09:00 · 09:30 · 10:00 · 10:30 · 11:00 · 11:30 |
| ⛅ Afternoon | 12:00 · 12:30 · 01:00 · 01:30 · 02:00 · 02:30 |
| 🌙 Evening | 03:00 · 03:30 · 04:00 · 04:30 · 05:00 · 05:30 |

- Past slots for today are automatically hidden
- Each slot can hold 1 booking (prevents double booking)
- Booked slots shown in red and disabled

---

## 🏥 Provider Details System

| Category | When provider shown | Details shown |
|---|---|---|
| Doctor | Before booking (on service & booking page) | Name, Phone, Education, Hospital, Address, Emergency Contact |
| Tutor | Before booking (on service & booking page) | Name, Phone, Education, Experience |
| Mechanic | After booking (in booking detail) | Name, Phone, Education, Experience, Workshop |
| Salon | After booking (in booking detail) | Name, Phone, Experience |
| Plumber | After booking (in booking detail) | Name, Phone, Experience |
| Electrician | After booking (in booking detail) | Name, Phone, Education, Experience, Working Details |
| Cleaner | After booking (in booking detail) | Name, Phone |
| Carpenter | After booking (in booking detail) | Name, Phone, Experience |

---

## ⭐ Review System

- Reviews only allowed after **booking status = Completed**
- Star rating UI (click to select 1–5 stars)
- Optional written comment
- One review per user per service
- Admin can update booking status to "Completed" from dashboard

---

## 🛡️ Tech Stack

| Component | Technology |
|---|---|
| Backend | Django 6.x (Python) |
| Database | SQLite3 |
| Frontend | Bootstrap 5.3 |
| Icons | Font Awesome 6.5 |
| Maps | Google Maps Embed API |
| Image handling | Pillow |
| Payment | UPI Deep Links (GPay, PhonePe, Paytm) |

---

## 📝 Notes

- Change `UPI_ID` in `settings.py` to your actual UPI ID for real payments
- For production, set `DEBUG = False` and configure a proper database
- Profile pictures and service images are stored in the `media/` folder
- The `Tutor` category has `online_only=True` — cash payment is not available

---

*Built with ❤️ using Django & Bootstrap 5 — SmartService Internship Project 2025*
