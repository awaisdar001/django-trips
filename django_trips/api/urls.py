"""Url definitions for api"""
from rest_framework import routers

from api.views import TripViewSet

router = routers.DefaultRouter()
router.register('trips', TripViewSet, 'trips')
urlpatterns = router.urls
