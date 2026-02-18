# main/admin.py
from pathlib import Path
import os
from django.contrib import admin
from django.apps import apps
from django.utils.html import format_html
from django import forms

from .models import AboutImage   # ✅ About section image


# Auto-detect the current app label (e.g., "main")
APP_LABEL = __name__.split(".")[0]


def get_model(name):
    """Return the model class for <APP_LABEL>.<name>, or None if it doesn't exist."""
    try:
        return apps.get_model(APP_LABEL, name)
    except LookupError:
        return None


def model_has_field(model, field_name: str) -> bool:
    try:
        model._meta.get_field(field_name)
        return True
    except Exception:
        return False


# =========================
# Base Mixin Classes
# =========================
class SafeFieldAdminMixin:
    """Auto-detect list_display, search_fields, list_filter. Adds previews for images/files.

    Behavior:
    - If `preferred_list_display` is set (non-empty), use that (and include preview thumb if configured).
    - Otherwise if the ModelAdmin subclass has an explicit `list_display` attribute, use that.
    - Otherwise fall back to default super().get_list_display(request).
    """

    preferred_list_display = ()
    preferred_search_fields = ()
    preferred_list_filter = ()
    preferred_date_hierarchy = None
    thumb_field = None  # e.g. "image" field name

    def _existing(self, fields):
        return [f for f in fields if model_has_field(self.model, f)]

    def get_list_display(self, request):
        # 1) If preferred_list_display is non-empty, use it (plus thumb if available)
        if getattr(self, "preferred_list_display", None):
            base = list(self._existing(self.preferred_list_display))
            if self.thumb_field and model_has_field(self.model, self.thumb_field):
                return ("_thumb",) + tuple(base)
            return tuple(base)

        # 2) If admin subclass explicitly set list_display, use it (don't override)
        if getattr(self, "list_display", None):
            return tuple(self.list_display)

        # 3) Fallback to default implementation
        return super().get_list_display(request)

    def _file_link(self, obj, fname):
        f = getattr(obj, fname, None)
        if not f:
            return "-"
        try:
            return format_html('<a href="{}" target="_blank">Open</a>', f.url)
        except Exception:
            return "-"

    def _image_tag(self, obj, fname, height=48):
        f = getattr(obj, fname, None)
        if not f:
            return "-"
        try:
            return format_html(
                '<img src="{}" style="height:{}px;border-radius:6px;object-fit:cover;">',
                f.url, height
            )
        except Exception:
            return "-"

    def _thumb(self, obj):
        if not self.thumb_field:
            return "-"
        return self._image_tag(obj, self.thumb_field)

    _thumb.short_description = "Preview"

    def get_search_fields(self, request):
        # prefer explicit preferred_search_fields, then explicit search_fields attribute, then default
        if getattr(self, "preferred_search_fields", None):
            return tuple(self._existing(self.preferred_search_fields))
        if getattr(self, "search_fields", None):
            return tuple(self.search_fields)
        return super().get_search_fields(request)

    def get_list_filter(self, request):
        if getattr(self, "preferred_list_filter", None):
            return tuple(self._existing(self.preferred_list_filter))
        if getattr(self, "list_filter", None):
            return tuple(self.list_filter)
        return super().get_list_filter(request)

    def get_date_hierarchy(self, request):
        dh = self.preferred_date_hierarchy
        return dh if dh and model_has_field(self.model, dh) else super().get_date_hierarchy(request)


class TimestampedReadOnlyMixin:
    """Automatically set created_at / updated_at as read-only if present."""
    def get_readonly_fields(self, request, obj=None):
        ro = list(getattr(super(), "get_readonly_fields", lambda *a, **k: [])(request, obj))
        for f in ("created_at", "updated_at"):
            if model_has_field(self.model, f) and f not in ro:
                ro.append(f)
        return tuple(ro)


Timetable = get_model("ClassTimetable")
if Timetable:
    @admin.register(Timetable)
    class ClassTimetableAdmin(SafeFieldAdminMixin, TimestampedReadOnlyMixin, admin.ModelAdmin):
        model = Timetable
        preferred_list_display = ("course", "semester", "academic_year", "pdf_preview", "created_at")
        preferred_search_fields = ("course", "academic_year")
        preferred_list_filter = ("course", "semester", "academic_year")
        preferred_date_hierarchy = "created_at"
        ordering = ("-created_at", "course", "semester")

        def pdf_preview(self, obj):
            return self._file_link(obj, "pdf_file")
        pdf_preview.short_description = "PDF"


# =========================
# Register Each Model
# =========================

# Slider
Slider = get_model("Slider")
if Slider:
    @admin.register(Slider)
    class SliderAdmin(SafeFieldAdminMixin, TimestampedReadOnlyMixin, admin.ModelAdmin):
        model = Slider
        thumb_field = "image"
        preferred_list_display = ("title", "is_active", "created_at")
        preferred_search_fields = ("title", "caption")
        preferred_list_filter = ("is_active",)
        preferred_date_hierarchy = "created_at"
        ordering = ("-created_at",)


# Exams
Exam = get_model("Exam")
if Exam:
    @admin.register(Exam)
    class ExamAdmin(SafeFieldAdminMixin, TimestampedReadOnlyMixin, admin.ModelAdmin):
        model = Exam
        preferred_list_display = ("title", "course", "semester", "exam_date", "pdf_preview")
        preferred_search_fields = ("title", "course")
        preferred_list_filter = ("course", "semester")
        preferred_date_hierarchy = "exam_date"
        ordering = ("exam_date", "semester")

        def pdf_preview(self, obj):
            return self._file_link(obj, "pdf_file")
        pdf_preview.short_description = "PDF"


# Events
Event = get_model("Event")
if Event:
    @admin.register(Event)
    class EventAdmin(SafeFieldAdminMixin, TimestampedReadOnlyMixin, admin.ModelAdmin):
        model = Event
        thumb_field = "image"
        preferred_list_display = ("title", "category", "start_at", "end_at", "venue", "is_registration_open", "video_preview")
        preferred_search_fields = ("title", "venue", "short_description")
        preferred_list_filter = ("category", "is_registration_open")
        preferred_date_hierarchy = "start_at"
        ordering = ("-start_at",)

        # show a link to uploaded video or external URL
        def video_preview(self, obj):
            if getattr(obj, "video", None):
                try:
                    return format_html('<a href="{}" target="_blank">🎬 Video File</a>', obj.video.url)
                except Exception:
                    return "-"
            if getattr(obj, "video_url", None):
                return format_html('<a href="{}" target="_blank">🔗 External</a>', obj.video_url)
            return "-"
        video_preview.short_description = "Video"

        # add helpful fields to the form view
        fieldsets = (
            ("Main", {"fields": ("title", "slug", "category", "short_description", "description")} ),
            ("When & Where", {"fields": ("start_at", "end_at", "venue")} ),
            ("Media", {"fields": ("image", "video", "video_url", "video_captions")} ),
            ("Registration", {"fields": ("is_registration_open",)}),
            ("Timestamps", {"classes": ("collapse",), "fields": ("created_at",)}),
        )

        readonly_fields = ("created_at",)


# News
News = get_model("News")
if News:
    @admin.register(News)
    class NewsAdmin(SafeFieldAdminMixin, TimestampedReadOnlyMixin, admin.ModelAdmin):
        model = News
        thumb_field = "image"
        preferred_list_display = ("title", "category", "published_at", "is_featured")
        preferred_search_fields = ("title", "summary")
        preferred_list_filter = ("category", "is_featured")
        preferred_date_hierarchy = "published_at"
        ordering = ("-published_at", "-id")

        actions = ("mark_featured", "unmark_featured")

        def mark_featured(self, request, queryset):
            queryset.update(is_featured=True)
        mark_featured.short_description = "Mark selected as featured"

        def unmark_featured(self, request, queryset):
            queryset.update(is_featured=False)
        unmark_featured.short_description = "Unmark selected as featured"


# Staff
StaffProfile = get_model("StaffProfile")
if StaffProfile:
    @admin.register(StaffProfile)
    class StaffProfileAdmin(SafeFieldAdminMixin, TimestampedReadOnlyMixin, admin.ModelAdmin):
        model = StaffProfile
        thumb_field = "photo"

        # Make order visible and editable in the list and include in form
        list_display = ("_thumb", "name", "role", "is_hod", "order", "phone", "email")
        list_display_links = ("name",)   # make name clickable
        list_editable = ("order",)      # allow quick inline editing of order
        search_fields = ("name", "email", "phone", "role")
        list_filter = ("role", "is_hod")
        ordering = ("-is_hod", "order", "role", "name")

        # fieldsets including 'order' so it shows in the change/add form
        fieldsets = (
            ("Identity", {"fields": ("name", "photo")}),
            ("Professional", {"fields": ("role", "designation", "qualifications", "specialization", "area", "bio", "is_hod", "order")}),
            ("Contact", {"fields": ("email", "phone", "profile_url")}),
            ("Timestamps", {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
        )

        readonly_fields = ("created_at", "updated_at")

        # Optional admin action to set selected staff as HOD (first selected)
        def make_hod(modeladmin, request, queryset):
            first = queryset.first()
            if not first:
                return
            # clear existing HOD flags
            StaffProfile.objects.exclude(pk=first.pk).filter(is_hod=True).update(is_hod=False)
            first.is_hod = True
            first.save()
            modeladmin.message_user(request, f"{first.name} is now set as HOD.")
        make_hod.short_description = "Set first selected staff as HOD"
        actions = (make_hod,)


# GalleryMedia
GalleryMedia = get_model("GalleryMedia")
if GalleryMedia:
    @admin.register(GalleryMedia)
    class GalleryMediaAdmin(SafeFieldAdminMixin, TimestampedReadOnlyMixin, admin.ModelAdmin):
        model = GalleryMedia
        thumb_field = "image"
        preferred_list_display = ("caption", "media_type", "year", "created_at")
        preferred_search_fields = ("caption",)
        preferred_list_filter = ("media_type", "year")
        ordering = ("-created_at", "-id")

        def preview(self, obj):
            """Show image thumbnail or video link in admin."""
            if getattr(obj, "media_type", None) == "photo" and getattr(obj, "image", None):
                return format_html(
                    '<img src="{}" style="height:60px;border-radius:8px;border:0;object-fit:cover;">',
                    obj.image.url,
                )
            elif getattr(obj, "media_type", None) == "video" and getattr(obj, "video", None):
                return format_html('<a href="{}" target="_blank">🎥 View Video</a>', obj.video.url)
            return "-"
        preview.short_description = "Preview"


# Contact Messages
ContactMessage = get_model("ContactMessage")
if ContactMessage:
    @admin.register(ContactMessage)
    class ContactMessageAdmin(SafeFieldAdminMixin, TimestampedReadOnlyMixin, admin.ModelAdmin):
        model = ContactMessage
        preferred_list_display = ("name", "email", "subject", "is_handled", "created_at")
        preferred_search_fields = ("name", "email", "subject")
        preferred_list_filter = ("is_handled",)
        preferred_date_hierarchy = "created_at"
        ordering = ("-created_at",)

        actions = ("mark_handled", "mark_unhandled")

        def mark_handled(self, request, queryset):
            queryset.update(is_handled=True)
        mark_handled.short_description = "Mark selected as handled"

        def mark_unhandled(self, request, queryset):
            queryset.update(is_handled=False)
        mark_unhandled.short_description = "Mark selected as unhandled"

        def get_readonly_fields(self, request, obj=None):
            ro = list(super().get_readonly_fields(request, obj))
            if "message" in [f.name for f in self.model._meta.fields]:
                ro.append("message")
            return tuple(ro)


# Department Settings
DepartmentSettings = get_model("DepartmentSettings")
if DepartmentSettings:
    @admin.register(DepartmentSettings)
    class DepartmentSettingsAdmin(TimestampedReadOnlyMixin, admin.ModelAdmin):
        model = DepartmentSettings

        def has_add_permission(self, request):
            """Only one DepartmentSettings instance allowed."""
            if self.model.objects.exists():
                return False
            return super().has_add_permission(request)

        def get_fields(self, request, obj=None):
            """Exclude id from form fields."""
            return [f.name for f in self.model._meta.fields if f.name != "id"]


# AboutImage
@admin.register(AboutImage)
class AboutImageAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "alt_text", "created_at", "preview")
    search_fields = ("title", "alt_text")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)

    fieldsets = (
        (None, {"fields": ("title", "image", "alt_text")} ),
        ("Timestamps", {"classes": ("collapse",), "fields": ("created_at",)}),
    )

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:8px;">', obj.image.url)
        return "-"
    preview.short_description = "Preview"

    def has_add_permission(self, request):
        """Allow only 1 AboutImage entry."""
        if AboutImage.objects.exists():
            return False
        return super().has_add_permission(request)


# -------------------------
# HighlightCard (admin + validation)
# -------------------------
HighlightCard = get_model("HighlightCard")
if HighlightCard:
    class HighlightCardForm(forms.ModelForm):
        """
        Enforce image presence and limit number of active highlight cards with images.
        Change MAX_ACTIVE to a different value to allow more cards.
        """
        MAX_ACTIVE = 3  # change this if you want more active highlight cards

        class Meta:
            model = HighlightCard
            fields = "__all__"

        def clean_image(self):
            img = self.cleaned_data.get("image")
            if not img:
                raise forms.ValidationError("Please upload an image for highlight cards.")
            return img

        def clean(self):
            cleaned = super().clean()
            is_active = cleaned.get("is_active")
            image = cleaned.get("image")
            # only validate active-count when saving an active card with an image
            if is_active and image:
                # count existing active highlight cards with images (exclude current pk if editing)
                qs = HighlightCard.objects.filter(is_active=True).exclude(pk=self.instance.pk)
                qs = qs.exclude(image__isnull=True).exclude(image__exact="")
                active_count = qs.count()
                if active_count >= self.MAX_ACTIVE:
                    raise forms.ValidationError(
                        f"Cannot mark active: there are already {active_count} active highlight cards. "
                        f"Maximum allowed is {self.MAX_ACTIVE}."
                    )
            return cleaned

    @admin.register(HighlightCard)
    class HighlightCardAdmin(SafeFieldAdminMixin, TimestampedReadOnlyMixin, admin.ModelAdmin):
        model = HighlightCard
        form = HighlightCardForm
        thumb_field = "image"

        # make explicit list_display so list_editable items are actually present
        list_display = ("_thumb", "title", "subtitle", "order", "is_active", "created_at")
        list_display_links = ("title",)   # clickable column (must not be editable)
        list_editable = ("order", "is_active")   # these MUST appear in list_display (they do)
        search_fields = ("title", "subtitle")
        list_filter = ("is_active",)
        ordering = ("order", "-created_at")

        fieldsets = (
            (None, {"fields": ("title", "subtitle", "image", "link")} ),
            ("Display", {"fields": ("order", "is_active")} ),
            ("Timestamps", {"classes": ("collapse",), "fields": ("created_at",)}),
        )

        def get_readonly_fields(self, request, obj=None):
            ro = list(super().get_readonly_fields(request, obj))
            if model_has_field(self.model, "created_at") and "created_at" not in ro:
                ro.append("created_at")
            return tuple(ro)


# -------------------------
# SectionImage (optional single-use section images, e.g., 'about' / 'bottom')
# -------------------------
SectionImage = get_model("SectionImage")
if SectionImage:
    @admin.register(SectionImage)
    class SectionImageAdmin(admin.ModelAdmin):
        model = SectionImage
        list_display = ("key", "title", "created_at", "preview")
        list_display_links = ("title",)
        search_fields = ("key", "title")
        ordering = ("-created_at",)
        readonly_fields = ("created_at",)
        fieldsets = (
            (None, {"fields": ("key", "title", "image", "alt_text")} ),
            ("Timestamps", {"classes": ("collapse",), "fields": ("created_at",)}),
        )

        def preview(self, obj):
            if getattr(obj, "image", None):
                return format_html('<img src="{}" style="height:60px;border-radius:8px;">', obj.image.url)
            return "-"
        preview.short_description = "Preview"

        def has_add_permission(self, request):
            """Optionally allow multiple keys but prevent duplicate key entries (if 'key' is present)."""
            return super().has_add_permission(request)


# =========================
# Admin Site Branding
# =========================
admin.site.site_header = "CS Department Administration"
admin.site.site_title = "CS Dept Admin"
admin.site.index_title = "Manage Website Content"
