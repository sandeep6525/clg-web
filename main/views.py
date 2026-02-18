from __future__ import annotations

from datetime import datetime
from typing import Optional
from math import ceil

from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

# New imports for admin/login decorators
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required

from .models import (
    ContactMessage,
    DepartmentSettings,
    Event,
    Exam,
    News,
    NewsCategory,
    StaffProfile,
    StaffRole,
    Slider,
    AboutImage,
    GalleryMedia,   # ✅ gallery model
    Album,          # ✅ album model
    HighlightCard,
    SectionImage,
    ClassTimetable,  # ← ADDED so timetables() can use the model
)


# -----------------------
# Small helpers
# -----------------------

def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.strptime(value, "%Y-%m-%d")
        return timezone.make_aware(dt)
    except Exception:
        return None


def _paginate(request: HttpRequest, queryset, per_page: int = 9, param_name: str = "page"):
    paginator = Paginator(queryset, per_page)
    page = request.GET.get(param_name)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    return page_obj, page_obj.object_list


def _repeat_for_scroll(items: list, min_items: int = 8) -> list:
    """Repeat the list until its length >= min_items."""
    if not items:
        return []
    repeats = ceil(min_items / len(items))
    return items * repeats


def _common_context() -> dict:
    """
    Return department settings, about image, bottom image and highlight cards for all templates.

    - about_image: prefers SectionImage with key='about', else latest SectionImage,
      else AboutImage fallback.
    - bottom_image: prefers SectionImage with key='bottom', else next most recent SectionImage.
    - highlight_cards: only active cards that have an image.
    """
    ctx = {
        "department_settings": DepartmentSettings.objects.first(),
        "about_image": AboutImage.objects.order_by("-created_at").first(),
    }

    try:
        # 1. Try by explicit keys
        about_section = SectionImage.objects.filter(key="about").order_by("-created_at").first()
        bottom_section = SectionImage.objects.filter(key="bottom").order_by("-created_at").first()

        # 2. Fallbacks: latest SectionImages
        if not about_section:
            about_section = SectionImage.objects.order_by("-created_at").first()
        if not bottom_section:
            bottom_section = (
                SectionImage.objects.exclude(pk=getattr(about_section, "pk", None))
                .order_by("-created_at")
                .first()
            )
    except Exception:
        about_section = None
        bottom_section = None

    ctx["about_image"] = about_section or ctx["about_image"]
    ctx["bottom_image"] = bottom_section

    try:
        cards_qs = list(
            HighlightCard.objects.filter(is_active=True)
            .exclude(image__isnull=True)
            .exclude(image__exact="")
            .order_by("order", "-created_at")
        )
    except Exception:
        cards_qs = []

    ctx["highlight_cards"] = _repeat_for_scroll(cards_qs, min_items=8)
    return ctx


# -----------------------
# Home
# -----------------------

def home(request: HttpRequest) -> HttpResponse:
    now = timezone.now()

    sliders = Slider.objects.filter(is_active=True).order_by("-created_at")[:8]
    next_exam = Exam.objects.filter(exam_date__gte=now.date()).order_by("exam_date", "semester").first()
    upcoming_event = Event.objects.filter(start_at__gte=now).order_by("start_at").first()
    latest_news = News.objects.order_by("-published_at", "-id").first()
    news_list = News.objects.order_by("-published_at", "-id")[:6]
    events_home = Event.objects.filter(start_at__gte=now).order_by("start_at")[:3]
    gallery_photos = GalleryMedia.objects.filter(media_type="photo").order_by("-created_at", "-id")[:8]

    context = {
        "sliders": sliders,
        "next_exam": next_exam,
        "upcoming_event": upcoming_event,
        "latest_news": latest_news,
        "news_list": news_list,
        "events_home": events_home,
        "gallery_photos": gallery_photos,
    }
    context.update(_common_context())
    return render(request, "main/home.html", context)


# -----------------------
# About
# -----------------------

def about(request: HttpRequest) -> HttpResponse:
    context = _common_context()
    return render(request, "main/about.html", context)


# -----------------------
# Staff
# -----------------------
def staff(request: HttpRequest) -> HttpResponse:
    """
    Staff listing view.

    - Shows ALL staff, ordered by the admin-defined `order` field.
    - Still keeps extra context if you want to use tabs later (hod_list, faculty, support).
    """
    q = request.GET.get("q", "").strip()
    role = request.GET.get("role", "").strip()

    staff_qs = StaffProfile.objects.all()

    # filters
    if q:
        staff_qs = staff_qs.filter(
            Q(name__icontains=q)
            | Q(email__icontains=q)
            | Q(area__icontains=q)
            | Q(specialization__icontains=q)
            | Q(designation__icontains=q)
        )
    if role:
        staff_qs = staff_qs.filter(role=role)

    # strict ordering by admin "order" field
    staff_qs = staff_qs.order_by("order", "role", "name")

    # subsets (optional – you can remove if you don’t use tabs)
    hod_list = staff_qs.filter(Q(is_hod=True) | Q(role=StaffRole.HOD))
    faculty = staff_qs.filter(role__in=[StaffRole.HOD, StaffRole.PROFESSOR, StaffRole.ASSOCIATE, StaffRole.ASSISTANT])
    support = staff_qs.filter(role__in=[StaffRole.INSTRUCTOR, StaffRole.TECH, StaffRole.SUPPORT])

    context = {
        "all_staff": staff_qs,   # ✅ this will include everyone
        "hod_list": hod_list,
        "faculty": faculty,
        "support": support,
    }
    context.update(_common_context())
    return render(request, "main/staff.html", context)

# -----------------------
# Events
# -----------------------

def events(request: HttpRequest) -> HttpResponse:
    now = timezone.now()
    q = request.GET.get("q", "").strip()
    type_ = request.GET.get("type", "").strip()
    dfrom = _parse_date(request.GET.get("from"))
    dto = _parse_date(request.GET.get("to"))

    base = Event.objects.all()

    if q:
        base = base.filter(
            Q(title__icontains=q)
            | Q(short_description__icontains=q)
            | Q(description__icontains=q)
            | Q(venue__icontains=q)
        )
    if type_:
        base = base.filter(category=type_)
    if dfrom:
        base = base.filter(start_at__date__gte=dfrom.date())
    if dto:
        base = base.filter(start_at__date__lte=dto.date())

    upcoming = base.filter(start_at__gte=now).order_by("start_at")
    past = base.filter(start_at__lt=now).order_by("-start_at")

    context = {
        "events_upcoming": list(upcoming[:18]),
        "events_past": list(past[:18]),
    }
    context.update(_common_context())
    return render(request, "main/events.html", context)


def event_detail(request: HttpRequest, slug: str) -> HttpResponse:
    obj = get_object_or_404(Event, slug=slug)
    related = Event.objects.filter(category=obj.category).exclude(pk=obj.pk).order_by("-start_at")[:4]
    context = {"event": obj, "related": related}
    context.update(_common_context())
    return render(request, "main/event_detail.html", context)


# -----------------------
# Exams
# -----------------------

def exams(request: HttpRequest) -> HttpResponse:
    q = request.GET.get("q", "").strip()
    semester = request.GET.get("semester", "").strip()
    dfrom_raw = request.GET.get("from", "").strip()

    exams_qs = Exam.objects.all()

    if q:
        exams_qs = exams_qs.filter(Q(title__icontains=q) | Q(course__icontains=q))
    if semester:
        try:
            exams_qs = exams_qs.filter(semester=int(semester))
        except ValueError:
            pass
    if dfrom_raw:
        try:
            dfrom = datetime.strptime(dfrom_raw, "%Y-%m-%d").date()
            exams_qs = exams_qs.filter(exam_date__gte=dfrom)
        except Exception:
            pass

    today = timezone.now().date()
    upcoming = exams_qs.filter(exam_date__gte=today).order_by("exam_date", "semester")
    past = exams_qs.filter(exam_date__lt=today).order_by("-exam_date")

    context = {
        "exams_upcoming": list(upcoming[:50]),
        "exams_past": list(past[:50]),
        "semesters": list(range(1, 9)),
    }
    context.update(_common_context())
    return render(request, "main/exams.html", context)


def timetables(request: HttpRequest) -> HttpResponse:
    q = request.GET.get("q", "").strip()
    semester = request.GET.get("semester", "").strip()
    year = request.GET.get("year", "").strip()

    qs = ClassTimetable.objects.all()

    if q:
        qs = qs.filter(course__icontains=q)
    if semester:
        try:
            qs = qs.filter(semester=int(semester))
        except ValueError:
            pass
    if year:
        qs = qs.filter(academic_year__icontains=year)

    qs = qs.order_by("-created_at")

    context = {
        "timetables": qs,
        "semesters": range(1, 9),
        "years": list(ClassTimetable.objects.values_list("academic_year", flat=True).distinct()),
    }
    context.update(_common_context())
    return render(request, "main/timetables.html", context)


# -----------------------
# News
# -----------------------

def news(request: HttpRequest) -> HttpResponse:
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    dfrom_raw = request.GET.get("from", "").strip()
    dto_raw = request.GET.get("to", "").strip()

    base = News.objects.all()

    if q:
        base = base.filter(Q(title__icontains=q) | Q(summary__icontains=q) | Q(body__icontains=q))
    if category:
        base = base.filter(category=category)
    if dfrom_raw:
        dfrom = _parse_date(dfrom_raw)
        if dfrom:
            base = base.filter(published_at__date__gte=dfrom.date())
    if dto_raw:
        dto = _parse_date(dto_raw)
        if dto:
            base = base.filter(published_at__date__lte=dto.date())

    base = base.order_by("-published_at", "-id")
    featured = base.filter(is_featured=True).first() or base.first()
    page_obj, news_items = _paginate(request, base, per_page=8)

    notices = News.objects.filter(category=NewsCategory.NOTICE).order_by("-published_at")[:6]
    categories = list(News.objects.values_list("category", flat=True).distinct())

    querydict = request.GET.copy()
    querydict.pop("page", None)
    qs = "&" + querydict.urlencode() if querydict else ""

    context = {
        "featured_news": featured,
        "news_list": news_items,
        "page_obj": page_obj,
        "querystring": qs,
        "categories": categories,
        "notices": notices,
    }
    context.update(_common_context())
    return render(request, "main/news.html", context)


def news_detail(request: HttpRequest, slug: str) -> HttpResponse:
    obj = get_object_or_404(News, slug=slug)
    recent = News.objects.exclude(pk=obj.pk).order_by("-published_at")[:6]
    context = {"item": obj, "recent": recent}
    context.update(_common_context())
    return render(request, "main/news_detail.html", context)


# -----------------------
# Gallery ✅
# -----------------------

def gallery(request):
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    year = request.GET.get("year", "").strip()

    items = GalleryMedia.objects.all()

    if q:
        items = items.filter(caption__icontains=q)
    if category:
        items = items.filter(media_type=category)
    if year:
        try:
            items = items.filter(year=int(year))
        except ValueError:
            pass

    items = items.order_by("-created_at", "-id")

    categories = ["photo", "video"]
    years = list(
        GalleryMedia.objects.exclude(year__isnull=True)
        .values_list("year", flat=True)
        .distinct()
        .order_by("-year")
    )

    # include albums for the albums section in the template
    albums = Album.objects.order_by("-created_at").all()

    page_obj, gallery_items = _paginate(request, items, per_page=18)

    querydict = request.GET.copy()
    querydict.pop("page", None)
    qs = "&" + querydict.urlencode() if querydict else ""

    context = {
        "gallery_items": gallery_items,
        "page_obj": page_obj,
        "querystring": qs,
        "categories": categories,
        "years": years,
        "albums": albums,
    }
    context.update(_common_context())
    return render(request, "main/gallery.html", context)


def album_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """
    Show a single album page with its media items (paginated).
    URL: /gallery/album/<slug>/
    """
    album = get_object_or_404(Album, slug=slug)

    q = request.GET.get("q", "").strip()
    items_qs = album.media.all().order_by("-created_at", "-id")  # related_name="media"

    if q:
        items_qs = items_qs.filter(caption__icontains=q)

    page_obj, gallery_items = _paginate(request, items_qs, per_page=18)

    querydict = request.GET.copy()
    querydict.pop("page", None)
    qs = "&" + querydict.urlencode() if querydict else ""

    context = {
        "album": album,
        "gallery_items": gallery_items,
        "page_obj": page_obj,
        "querystring": qs,
    }
    context.update(_common_context())
    return render(request, "main/album_detail.html", context)


# -----------------------
# New: Gallery admin + upload placeholders
# -----------------------

@staff_member_required
def gallery_admin(request: HttpRequest) -> HttpResponse:
    """
    Staff-only gallery admin placeholder.
    Expand this view to list albums, provide upload/edit/delete forms, etc.
    """
    # Example: you might want to pass albums, pending uploads, or forms here.
    context = {
        "message": "Gallery admin placeholder — implement create/edit UI here.",
    }
    context.update(_common_context())
    return render(request, "main/gallery_admin.html", context)


@login_required
def upload_media(request: HttpRequest) -> HttpResponse:
    """
    Simple upload placeholder. Replace with a proper ModelForm to handle image/video uploads.
    """
    if request.method == "POST":
        # TODO: validate and save the uploaded file(s) using a ModelForm and GalleryMedia model.
        # For now, redirect back to gallery with a success message.
        messages.success(request, "Upload placeholder: implement upload handling (ModelForm) to save files.")
        return redirect("gallery")  # redirect to the non-namespaced URL name

    context = {}
    context.update(_common_context())
    return render(request, "main/upload_media.html", context)


# -----------------------
# Contact
# -----------------------

def contact(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        subject = request.POST.get("subject", "").strip()
        message = request.POST.get("message", "").strip()

        if not (name and email and subject and message):
            messages.warning(request, "Please fill all required fields.")
            return redirect("contact")

        ContactMessage.objects.create(
            name=name, email=email, phone=phone, subject=subject, message=message
        )
        messages.success(request, "Thanks! Your message has been sent.")
        return redirect("contact")

    context = {"form": {}}
    context.update(_common_context())
    return render(request, "main/contact.html", context)
