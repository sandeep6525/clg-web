from django.urls import path
from . import views

urlpatterns = [
# ---------------- Home & About ----------------
path("", views.home, name="home"),
path("about/", views.about, name="about"),
path("staff/", views.staff, name="staff"),


# ---------------- Events ----------------
path("events/", views.events, name="events"),
path("events/<slug:slug>/", views.event_detail, name="event_detail"),

# ---------------- Exams ----------------
path("exams/", views.exams, name="exams"),
# Timetables
path("timetables/", views.timetables, name="timetables"),

# ---------------- News ----------------
path("news/", views.news, name="news"),
path("news/<slug:slug>/", views.news_detail, name="news_detail"),

# ---------------- Gallery ----------------
path("gallery/", views.gallery, name="gallery"),
path("gallery/admin/", views.gallery_admin, name="gallery_admin"),   # ✅ added
path("gallery/upload/", views.upload_media, name="upload_media"),   # ✅ added
path("gallery/album/<slug:slug>/", views.album_detail, name="album_detail"),  # ✅ added

# ---------------- Contact ----------------
path("contact/", views.contact, name="contact"),


]
