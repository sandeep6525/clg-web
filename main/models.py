from __future__ import annotations

import os
import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_save
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone

# ---------- Small helpers ----------
def year_choices(start: int = 2000) -> list[tuple[int, int]]:
    this = timezone.now().year
    return [(y, y) for y in range(this, start - 1, -1)]


def _unique_name(prefix: str, filename: str) -> str:
    base, ext = os.path.splitext(filename)
    return f"{prefix}/{uuid.uuid4().hex}{ext.lower()}"


# ---------- upload_to functions ----------
def settings_upload(instance, filename): return _unique_name("settings", filename)
def slides_upload(instance, filename):   return _unique_name("slides", filename)
def exams_upload(instance, filename):    return _unique_name("exams", filename)
def events_upload(instance, filename):   return _unique_name("events", filename)
def news_upload(instance, filename):     return _unique_name("news", filename)
def staff_upload(instance, filename):    return _unique_name("staff", filename)
def photos_upload(instance, filename):   return _unique_name("gallery/photos", filename)
def slider_upload(instance, filename):   return _unique_name("sliders", filename)
def slider_video_upload(instance, filename): return _unique_name("sliders/videos", filename)
def about_upload(instance, filename):    return _unique_name("about", filename)

# New upload helpers for highlights/sections
def highlight_upload(instance, filename): return _unique_name("highlights", filename)
def section_upload(instance, filename):   return _unique_name("sections", filename)


# ---------- Department Settings ----------
class DepartmentSettings(models.Model):
    site_name = models.CharField(max_length=255, blank=True, null=True)
    logo = models.ImageField(upload_to=settings_upload, blank=True, null=True)
    about_short = models.TextField(blank=True)
    address = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    instagram = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    x_twitter = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "⚙️ Department Setting"
        verbose_name_plural = "⚙️ Department Settings"

    def __str__(self):
        return self.site_name if self.site_name else "Department Settings"

    def delete(self, *args, **kwargs):
        if self.logo:
            self.logo.delete(save=False)
        super().delete(*args, **kwargs)


# ---------- Slider ----------
class Slider(models.Model):
    title = models.CharField(max_length=200, blank=True, null=True)
    image = models.ImageField(upload_to=slider_upload, blank=True, null=True)
    video = models.FileField(upload_to=slider_video_upload, blank=True, null=True)
    caption = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "🎞️ Slider"
        verbose_name_plural = "🎞️ Sliders"

    def __str__(self):
        return self.title or f"Slider {self.id}"

    def clean(self):
        if not self.image and not self.video:
            raise ValidationError("Please provide either an image or a video for the slider.")

    def delete(self, *args, **kwargs):
        if self.image:
            self.image.delete(save=False)
        if self.video:
            self.video.delete(save=False)
        super().delete(*args, **kwargs)


# ---------- About Section Image ----------
class AboutImage(models.Model):
    title = models.CharField(max_length=150, blank=True)
    image = models.ImageField(upload_to=about_upload)
    alt_text = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "🖼 About Image"
        verbose_name_plural = "🖼 About Images"

    def save(self, *args, **kwargs):
        if not self.pk and AboutImage.objects.exists():
            AboutImage.objects.all().delete()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or f"About Image {self.id}"

    def delete(self, *args, **kwargs):
        if self.image:
            self.image.delete(save=False)
        super().delete(*args, **kwargs)


# ---------- Highlight Card (for moving row) ----------
class HighlightCard(models.Model):
    title = models.CharField(max_length=150, blank=True)
    subtitle = models.CharField(max_length=250, blank=True)
    image = models.ImageField(upload_to=highlight_upload, blank=True, null=True)
    link = models.URLField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("order", "-created_at")
        verbose_name = "✨ Highlight Card"
        verbose_name_plural = "✨ Highlight Cards"

    def __str__(self):
        return self.title or f"Highlight {self.pk}"

    def delete(self, *args, **kwargs):
        if self.image:
            self.image.delete(save=False)
        super().delete(*args, **kwargs)


# ---------- SectionImage (single-key images like bottom/about) ----------
class SectionImage(models.Model):
    """
    Optional keyed section images. Use keys like 'bottom', 'about' etc.
    Views can pick the latest entry for a key: SectionImage.objects.filter(key='bottom').first()
    """
    key = models.CharField(max_length=50, help_text="Unique key for section (e.g. 'bottom', 'about')")
    title = models.CharField(max_length=150, blank=True)
    image = models.ImageField(upload_to=section_upload)
    alt_text = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "🖼 Section Image"
        verbose_name_plural = "🖼 Section Images"

    def __str__(self):
        return f"{self.key} — {self.title or self.pk}"

    def delete(self, *args, **kwargs):
        if self.image:
            self.image.delete(save=False)
        super().delete(*args, **kwargs)


# ---------- Exams ----------
class Exam(models.Model):
    title = models.CharField(max_length=200)
    course = models.CharField(max_length=120, help_text="e.g., B.Sc CS / BCA / M.Sc CS")
    semester = models.PositiveSmallIntegerField(choices=[(i, f"Semester {i}") for i in range(1, 9)])
    exam_date = models.DateField()
    pdf_file = models.FileField(upload_to=exams_upload, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("exam_date", "semester")
        verbose_name = "📋 Exam"
        verbose_name_plural = "📋 Exams"

    def __str__(self):
        return f"{self.title} (S{self.semester})"

    def clean(self):
        if self.exam_date and self.exam_date.year < 2000:
            raise ValidationError({"exam_date": "Exam date looks invalid."})

    def delete(self, *args, **kwargs):
        if self.pdf_file:
            self.pdf_file.delete(save=False)
        super().delete(*args, **kwargs)


# ---------- Class Timetable ----------
def timetable_upload(instance, filename):
    return _unique_name("timetables", filename)

class ClassTimetable(models.Model):
    course = models.CharField(max_length=120, help_text="e.g., B.Sc CS / BCA / M.Sc CS")
    semester = models.PositiveSmallIntegerField(choices=[(i, f"Semester {i}") for i in range(1, 9)])
    academic_year = models.CharField(max_length=20, help_text="e.g., 2024-2025")
    pdf_file = models.FileField(upload_to=timetable_upload, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "course", "semester")
        verbose_name = "📅 Class Timetable"
        verbose_name_plural = "📅 Class Timetables"

    def __str__(self):
        return f"{self.course} S{self.semester} ({self.academic_year})"

    def delete(self, *args, **kwargs):
        if self.pdf_file:
            self.pdf_file.delete(save=False)
        super().delete(*args, **kwargs)

# ---------- Events ----------
class EventCategory(models.TextChoices):
    WORKSHOP = "Workshop", "Workshop"
    SEMINAR = "Seminar", "Seminar"
    SYMPOSIUM = "Symposium", "Symposium"
    COMPETITION = "Competition", "Competition"
    GUEST = "Guest Lecture", "Guest Lecture"
    OTHER = "Other", "Other"


class Event(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    category = models.CharField(max_length=32, choices=EventCategory.choices, default=EventCategory.OTHER)
    short_description = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField(blank=True, null=True)
    venue = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to=events_upload, blank=True, null=True)

    # --- NEW: video support ---
    video = models.FileField(upload_to=events_upload, blank=True, null=True, help_text="Self-hosted video file (MP4/WebM).")
    video_url = models.URLField(blank=True, null=True, help_text="External video URL (YouTube / Vimeo).")
    video_captions = models.FileField(upload_to=events_upload, blank=True, null=True, help_text="Optional VTT captions file.")

    is_registration_open = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-start_at",)
        verbose_name = "🎉 Event"
        verbose_name_plural = "🎉 Events"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("event_detail", kwargs={"slug": self.slug})

    @property
    def is_past(self) -> bool:
        ends = self.end_at or self.start_at
        return ends < timezone.now()

    def has_video(self) -> bool:
        """Return True if this event has any associated video (self-hosted or external)."""
        return bool(self.video) or bool(self.video_url)

    def get_embed_url(self) -> str | None:
        """Return a normalized embeddable URL for known providers (YouTube, Vimeo).

        Falls back to the raw video_url when a specific embed pattern isn't found.
        """
        if not self.video_url:
            return None
        import re
        url = self.video_url.strip()
        # YouTube: handle youtube.com/watch?v=ID and youtu.be/ID
        m = re.search(r'(?:v=|youtu\.be/)([A-Za-z0-9_\-]{6,})', url)
        if m:
            return f'https://www.youtube.com/embed/{m.group(1)}'
        # Vimeo: handle vimeo.com/ID and player.vimeo.com/video/ID
        m = re.search(r'vimeo\.com/(?:video/)?(\d+)', url)
        if m:
            return f'https://player.vimeo.com/video/{m.group(1)}'
        # Fallback - return the provided URL (some services may allow iframe src directly)
        return url

    def clean(self):
        if self.end_at and self.start_at and self.end_at < self.start_at:
            raise ValidationError({"end_at": "End time must be after start time."})

    def delete(self, *args, **kwargs):
        # remove uploaded media files when deleting the event
        if self.image:
            self.image.delete(save=False)
        if self.video:
            self.video.delete(save=False)
        if self.video_captions:
            self.video_captions.delete(save=False)
        super().delete(*args, **kwargs)


# ---------- News ----------
class NewsCategory(models.TextChoices):
    ANNOUNCEMENT = "Announcement", "Announcement"
    ACHIEVEMENT = "Achievement", "Achievement"
    PLACEMENT = "Placement", "Placement"
    RESEARCH = "Research", "Research"
    NOTICE = "Notice", "Notice"
    GENERAL = "General", "General"


class News(models.Model):
    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    category = models.CharField(max_length=20, choices=NewsCategory.choices, default=NewsCategory.GENERAL)
    summary = models.TextField(blank=True)
    body = models.TextField(blank=True)
    image = models.ImageField(upload_to=news_upload, blank=True, null=True)
    published_at = models.DateTimeField(auto_now_add=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ("-published_at", "-id")
        verbose_name = "📰 News"
        verbose_name_plural = "📰 News"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("news_detail", kwargs={"slug": self.slug})

    def delete(self, *args, **kwargs):
        if self.image:
            self.image.delete(save=False)
        super().delete(*args, **kwargs)


# ---------- Staff ----------
class StaffRole(models.TextChoices):
    HOD = "HOD", "HOD"
    PROFESSOR = "Professor", "Professor"
    ASSOCIATE = "Associate Professor", "Associate Professor"
    ASSISTANT = "Assistant Professor", "Assistant Professor"
    INSTRUCTOR = "Lab Instructor", "Lab Instructor"
    TECH = "Technical Staff", "Technical Staff"
    SUPPORT = "Support", "Support"


class StaffProfile(models.Model):
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=32, choices=StaffRole.choices, default=StaffRole.ASSISTANT)
    designation = models.CharField(max_length=120, blank=True)
    qualifications = models.CharField(max_length=200, blank=True)
    specialization = models.CharField(max_length=200, blank=True)
    area = models.CharField(max_length=200, blank=True, help_text="Area of interest / expertise")
    bio = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    profile_url = models.URLField(blank=True)
    photo = models.ImageField(upload_to=staff_upload, blank=True, null=True)

    # Keep the explicit HoD flag
    is_hod = models.BooleanField(default=False)

    # NEW: manual ordering priority (lower appears earlier after HoD)
    order = models.PositiveSmallIntegerField(default=0, help_text="Manual ordering priority (lower appears earlier)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # -is_hod makes True appear first, then by `order`, then role, then name
        ordering = ("-is_hod", "order", "role", "name")
        verbose_name = "👩‍🏫 Staff Profile"
        verbose_name_plural = "👨‍🏫 Staff Profiles"

    def __str__(self):
        return f"{self.name} — {self.role}"

    def delete(self, *args, **kwargs):
        if self.photo:
            self.photo.delete(save=False)
        super().delete(*args, **kwargs)


# ---------- Album (NEW) ----------
class Album(models.Model):
    """
    Simple album model for grouping gallery media.
    Used by templates (album.id, album.title, album.slug, album.cover_image, album.year, album.category).
    """
    CATEGORY_CHOICES = (
        ("event", "Event"),
        ("workshop", "Workshop"),
        ("annual", "Annual"),
        ("misc", "Miscellaneous"),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    cover_image = models.ImageField(upload_to=photos_upload, blank=True, null=True)
    year = models.PositiveIntegerField(choices=year_choices(), blank=True, null=True)
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "🗂️ Album"
        verbose_name_plural = "🗂️ Albums"

    def __str__(self):
        return self.title or f"Album {self.pk}"

    def get_absolute_url(self):
        return reverse("album_detail", kwargs={"slug": self.slug})

    def delete(self, *args, **kwargs):
        if self.cover_image:
            self.cover_image.delete(save=False)
        super().delete(*args, **kwargs)


# ---------- Gallery (updated to reference album) ----------
class GalleryMedia(models.Model):
    MEDIA_TYPES = (
        ("photo", "Photo"),
        ("video", "Video"),
    )
    album = models.ForeignKey(Album, on_delete=models.SET_NULL, blank=True, null=True, related_name="media")
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES, default="photo")
    image = models.ImageField(upload_to=photos_upload, blank=True, null=True)
    video = models.FileField(upload_to="gallery/videos/", blank=True, null=True)
    caption = models.CharField(max_length=200, blank=True)
    year = models.PositiveIntegerField(choices=year_choices(), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name = "📸 Gallery Media"
        verbose_name_plural = "📸 Gallery Media"

    def __str__(self):
        return self.caption or f"Media #{self.id}"

    def delete(self, *args, **kwargs):
        if self.image:
            self.image.delete(save=False)
        if self.video:
            self.video.delete(save=False)
        super().delete(*args, **kwargs)


# ---------- Contact ----------
class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_handled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "📩 Contact Message"
        verbose_name_plural = "📩 Contact Messages"

    def __str__(self):
        return f"{self.subject} — {self.name}"


# ---------- Slug & HOD Utilities ----------
def _unique_slug(instance, field_name: str, slug_field: str = "slug", max_length: int | None = None):
    base = getattr(instance, slug_field, "") or slugify(getattr(instance, field_name, "") or "")
    base = base[: (max_length or 240)]
    if not base:
        base = uuid.uuid4().hex[:8]
    slug = base
    Model = type(instance)
    n = 2
    while Model.objects.filter(**{slug_field: slug}).exclude(pk=instance.pk).exists():
        suffix = f"-{n}"
        cut = (max_length or 240) - len(suffix)
        slug = f"{base[:cut]}{suffix}"
        n += 1
    setattr(instance, slug_field, slug)


def _ensure_single_hod(sender, instance: StaffProfile, **kwargs):
    if instance.is_hod or instance.role == StaffRole.HOD:
        StaffProfile.objects.exclude(pk=instance.pk).filter(
            models.Q(is_hod=True) | models.Q(role=StaffRole.HOD)
        ).update(is_hod=False, role=StaffRole.PROFESSOR)



def _pre_slug(sender, instance, **kwargs):
    if isinstance(instance, Event) and not instance.slug:
        _unique_slug(instance, "title", "slug", max_length=220)
    if isinstance(instance, News) and not instance.slug:
        _unique_slug(instance, "title", "slug", max_length=240)
    # Album slugs
    if isinstance(instance, Album) and not instance.slug:
        _unique_slug(instance, "title", "slug", max_length=240)


# Connect signals
pre_save.connect(_pre_slug, sender=Event)
pre_save.connect(_pre_slug, sender=News)
pre_save.connect(_pre_slug, sender=Album)
pre_save.connect(_ensure_single_hod, sender=StaffProfile)
