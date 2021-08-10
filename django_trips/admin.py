# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django_trips.models import (CancellationPolicy, Facility, Host, Location,
                                 Trip, TripBooking, TripItinerary,
                                 TripPickupLocation, TripReview,
                                 TripReviewSummary, TripSchedule)


class TripScheduleAdminInline(admin.TabularInline):
    """Trip schedule inline modal admin"""
    model = TripSchedule
    extra = 0


class TripReviewSummaryInline(admin.StackedInline):
    model = TripReviewSummary
    extra = 0


class TripItineraryAdminInline(admin.StackedInline):
    """Trip itinerary inline modal admin"""
    model = TripItinerary
    extra = 0


admin.register(CancellationPolicy)


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    """Trip modal admin configuration"""
    inlines = [TripItineraryAdminInline, TripScheduleAdminInline, TripReviewSummaryInline]
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'slug',)
    list_filter = ('destination',)
    search_fields = ['name', 'description', 'slug', 'locations__name']


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    """Facility modal admin configuration"""
    prepopulated_fields = {'slug': ('name',)}
    list_display = (
        'name', 'slug',
    )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """Location modal admin configuration"""
    prepopulated_fields = {'slug': ('name',)}
    list_display = (
        'name', 'slug',
    )
    list_filter = ('is_destination', 'is_departure', 'deleted')


@admin.register(TripItinerary)
class TripItineraryAdmin(admin.ModelAdmin):
    """Trip itinerary modal admin configuration"""
    list_display = ('trip', 'description')
    list_filter = ('trip',)
    search_fields = ['trip']


@admin.register(TripSchedule)
class TripScheduleAdmin(admin.ModelAdmin):
    """Trip schedule admin configuration"""
    list_display = ('trip', 'date_from')
    list_filter = ('date_from',)
    search_fields = ['trip']


@admin.register(Host)
class HostAdmin(admin.ModelAdmin):
    """Host modal admin configuration"""
    list_display = (
        'name', 'description', 'verified'
    )
    list_filter = ('verified',)
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(TripReview)
class TripReviewAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'trip', 'meals', 'accommodation', 'transport',
        'value_for_money', 'overall',
    )
    list_filter = ('is_verified', 'trip', 'overall')
    search_fields = ['trip__name', 'name']


@admin.register(TripReviewSummary)
class TripReviewSummaryAdmin(admin.ModelAdmin):
    # inlines = (TripInline,)
    list_display = (
        'trip', 'meals', 'accommodation', 'transport',
        'value_for_money', 'overall',
    )
    list_filter = ('overall',)
    search_fields = ['trip__name']


@admin.register(TripPickupLocation)
class TripPickupLocationAdmin(admin.ModelAdmin):
    list_display = (
        'trip', 'location', 'additional_price'
    )
    search_fields = ['trip__name']
    list_filter = ('location',)


@admin.register(TripBooking)
class TripBookingSummaryAdmin(admin.ModelAdmin):
    list_display = ('name', 'schedule', 'phone_number', 'message')
    search_fields = ['schedule__trip__name', 'name']
    list_filter = ('schedule__trip__name', 'schedule__date_from')
