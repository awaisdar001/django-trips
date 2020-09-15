# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from trips.models import (Activity, Facility, Host, Location, Trip, TripItinerary,
                          TripSchedule)


class TripScheduleAdminInline(admin.TabularInline):
    """Trip schedule inline modal admin"""
    model = TripSchedule
    extra = 0


class TripItineraryAdminInline(admin.StackedInline):
    """Trip itinerary inline modal admin"""
    model = TripItinerary
    extra = 0


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    """Trip modal admin configuration"""
    inlines = [TripItineraryAdminInline, TripScheduleAdminInline]
    prepopulated_fields = {'slug': ('name',)}
    list_display = (
        'name', 'slug', 'price'
    )
    list_filter = ('starting_location',)
    search_fields = ['name', 'description', 'locations_included']


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    """Activity modal admin configuration"""
    prepopulated_fields = {'slug': ('name',)}
    list_display = (
        'name', 'slug',
    )


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
