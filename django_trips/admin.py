"""Django admin config"""

from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from django_trips.choices import LocationType
from django_trips.models import (
    CancellationPolicy,
    Category,
    Facility,
    Gear,
    Host,
    HostRating,
    HostType,
    Location,
    Testimonial,
    Trip,
    TripAvailability,
    TripBooking,
    TripImage,
    TripItinerary,
    TripPackage,
    TripPickupLocation,
    TripReview,
    TripReviewSummary,
    TripSchedule,
    TripWishlist,
    TrustBadge,
)


class TripScheduleAdminInline(admin.TabularInline):
    """Trip schedule inline modal admin"""

    model = TripSchedule
    extra = 0


class TripAvailabilityAdminInline(admin.TabularInline):
    """Trip schedule inline modal admin"""

    model = TripAvailability
    extra = 0


class HostRatingInline(admin.StackedInline):
    model = HostRating
    extra = 0


class TripReviewSummaryInline(admin.StackedInline):
    model = TripReviewSummary
    extra = 0


class TripItineraryAdminInline(admin.StackedInline):
    """Trip itinerary inline modal admin"""

    model = TripItinerary
    extra = 0


class TripImageAdminInline(admin.TabularInline):
    """Trip photo gallery inline modal admin"""

    model = TripImage
    extra = 1


admin.site.register(CancellationPolicy, ConfigurationModelAdmin)


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    """Trip modal admin configuration"""

    inlines = [
        TripAvailabilityAdminInline,
        TripImageAdminInline,
        TripItineraryAdminInline,
        TripScheduleAdminInline,
        TripReviewSummaryInline,
    ]

    def get_date(self, trip):
        return [availability.end_date for availability in trip.availabilities.all()]

    get_date.short_description = "Availability Up to"

    prepopulated_fields = {"slug": ("name",)}
    list_display = (
        "name",
        "host",
        "departure",
        "destination",
        "featured",
        "get_date",
    )
    list_filter = (
        "availabilities__type",
        "destination",
        "featured",
        "host",
    )
    search_fields = ["name", "description", "slug", "locations__name"]


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    """Facility modal admin configuration"""

    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "slug"]
    list_display = (
        "name",
        "slug",
        "icon",
    )


@admin.register(TrustBadge)
class TrustBadgeAdmin(admin.ModelAdmin):
    """Trust badge modal admin configuration"""

    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "slug"]
    list_display = (
        "name",
        "slug",
        "icon",
    )


class RegionListFilter(admin.SimpleListFilter):
    """Filters the Location changelist down to children of a chosen region."""

    title = "region"
    parameter_name = "parent"

    def lookups(self, request, model_admin):
        regions = Location.objects.filter(type=LocationType.REGION).order_by("name")
        return [(region.pk, region.name) for region in regions]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(parent__id=self.value())
        return queryset


class ProvinceListFilter(admin.SimpleListFilter):
    """Filters the Location changelist down to children of a chosen province."""

    title = "province"
    parameter_name = "parent"

    def lookups(self, request, model_admin):
        provinces = Location.objects.filter(type=LocationType.PROVINCE).order_by("name")
        return [(province.pk, province.name) for province in provinces]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(parent__id=self.value())
        return queryset


class LocationChildInline(admin.TabularInline):
    """Inline listing of a Location's children (e.g. a region's cities)."""

    model = Location
    fk_name = "parent"
    extra = 0
    fields = ("name", "slug", "type", "is_active")
    show_change_link = True
    verbose_name = "Child location"
    verbose_name_plural = "Child locations"


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """Location modal admin configuration"""

    prepopulated_fields = {"slug": ("name",)}
    list_display = (
        "name",
        "slug",
        "type",
        "parent",
    )
    list_filter = ("is_active", "type", ProvinceListFilter, RegionListFilter)
    search_fields = ["name", "slug"]
    autocomplete_fields = ["parent"]
    inlines = [LocationChildInline]


@admin.register(TripItinerary)
class TripItineraryAdmin(admin.ModelAdmin):
    """Trip itinerary modal admin configuration"""

    list_display = ("trip", "description")
    list_filter = ("trip",)
    search_fields = ["trip"]


@admin.register(TripSchedule)
class TripScheduleAdmin(admin.ModelAdmin):
    """Trip schedule admin configuration"""

    list_display = (
        "trip",
        "status",
        "price",
        "child_price",
        "start_date",
        "end_date",
    )
    list_filter = (
        "start_date",
        "end_date",
        "status",
        "price",
    )
    search_fields = ("trip", "status")
    raw_id_fields = ("trip",)


@admin.action(
    description="Mark selected hosts as inactive (and deactivate their trips)"
)
def deactivate_hosts(modeladmin, request, queryset):
    trips_updated = Trip.objects.filter(host__in=queryset).update(is_active=False)
    hosts_updated = queryset.update(is_active=False)
    modeladmin.message_user(
        request,
        f"Deactivated {hosts_updated} host(s) and {trips_updated} of their trip(s).",
    )


@admin.register(Host)
class HostAdmin(admin.ModelAdmin):
    """Host modal admin configuration"""

    inlines = [HostRatingInline]
    actions = [deactivate_hosts]
    list_display = ("name", "description", "verified", "is_active")
    list_filter = ("verified", "is_active")
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(TripReview)
class TripReviewAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "trip",
        "location",
        "meals",
        "accommodation",
        "transport",
        "value_for_money",
        "overall",
        "is_verified",
    )
    list_filter = ("is_verified", "trip", "overall")
    search_fields = ["trip__name", "name"]


@admin.register(TripReviewSummary)
class TripReviewSummaryAdmin(admin.ModelAdmin):
    # inlines = (TripInline,)
    list_display = (
        "trip",
        "meals",
        "accommodation",
        "transport",
        "value_for_money",
        "overall",
    )
    list_filter = ("overall",)
    search_fields = ["trip__name"]


@admin.action(description="Mark selected testimonials as active")
def activate_testimonials(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(request, f"Marked {updated} testimonial(s) as active.")


@admin.action(description="Mark selected testimonials as inactive")
def deactivate_testimonials(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(request, f"Marked {updated} testimonial(s) as inactive.")


@admin.action(description="Mark selected testimonials as verified")
def verify_testimonials(modeladmin, request, queryset):
    updated = queryset.update(is_verified=True)
    modeladmin.message_user(request, f"Marked {updated} testimonial(s) as verified.")


@admin.action(description="Mark selected testimonials as unverified")
def unverify_testimonials(modeladmin, request, queryset):
    updated = queryset.update(is_verified=False)
    modeladmin.message_user(request, f"Marked {updated} testimonial(s) as unverified.")


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "is_verified", "is_active", "created_at")
    list_filter = ("is_verified", "is_active")
    search_fields = ["name", "quote"]
    actions = [
        activate_testimonials,
        deactivate_testimonials,
        verify_testimonials,
        unverify_testimonials,
    ]


@admin.register(TripPackage)
class TripPackageAdmin(admin.ModelAdmin):
    """Trip pricing package (Standard/Budget/Premium) admin configuration"""

    list_display = ("trip", "name", "additional_price", "additional_child_price")
    list_filter = ("name",)
    search_fields = ["trip__name"]


@admin.register(TripPickupLocation)
class TripPickupLocationAdmin(admin.ModelAdmin):
    list_display = ("schedule", "location", "additional_price")
    search_fields = ["schedule__trip__name"]
    list_filter = ("location",)


@admin.register(TripBooking)
class TripBookingSummaryAdmin(admin.ModelAdmin):
    list_display = ("full_name", "schedule", "phone_number", "message")
    search_fields = ["schedule__trip__name", "name"]
    list_filter = ("schedule__trip__name", "target_date")


@admin.register(TripWishlist)
class TripWishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "trip", "created_at")
    search_fields = ["user__username", "trip__name"]
    list_filter = ("created_at",)


@admin.register(HostType)
class HostTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ["name"]


@admin.register(TripAvailability)
class TripAvailabilityAdmin(admin.ModelAdmin):
    list_display = (
        "trip",
        "type",
        "price",
        "start_date",
        "end_date",
    )
    list_filter = (
        "type",
        "start_date",
        "end_date",
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "icon")
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Gear)
class GearAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}
