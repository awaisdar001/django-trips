from django.db import models


class TripOptions(models.TextChoices):
    STANDARD = "STANDARD", "Standard Package"
    BUDGET = "BUDGET", "Standard Package"
    PREMIUM = "PREMIUM", "Premium Package"


class LocationType(models.TextChoices):
    TOWN = "TOWN", "Town"
    CITY = "CITY", "City"
    PROVINCE = "PROVINCE", "Province"


class AvailabilityType(models.TextChoices):
    DAILY = "DAILY", "Daily"
    WEEKLY = "WEEKLY", "Weekly"
    MONTHLY = "MONTHLY", "Monthly"
    FIX_DATE = "FIX_DATE", "Fix Date"


class ScheduleStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    CANCELLED = "cancelled", "Cancelled"
    FULL = "full", "Fully Booked"


class BookingStatus(models.TextChoices):
    """
    Represents the lifecycle states of a booking with allowed transitions.

    Status Flow:
    └── PENDING
        ├── WAITING_PAYMENT (when payment required)
        │   ├── CONFIRMED (on full payment)
        │   │   ├── COMPLETED (after trip completion)
        │   │   └── CANCELLED (admin-initiated only + refund)
        │   └── CANCELLED (if payment not received)
        ├── CONFIRMED (if no payment required)
        │   ├── COMPLETED
        │   └── CANCELLED (admin-initiated)
        └── CANCELLED (user-initiated while pending)

    Special Cases:
    - PARTIAL_PAYMENT: Can only transition from WAITING_PAYMENT
        └── Either progresses to CONFIRMED (on full payment)
            or falls back to CANCELLED

    Restrictions:
    - CONFIRMED/COMPLETED/PARTIAL_PAYMENT bookings cannot be automatically cancelled
    - Only admin can cancel these bookings
    - PENDING/WAITING_PAYMENT bookings can be user-cancelled
    """

    PENDING = "PENDING", "Pending"
    WAITING_PAYMENT = "WAITING_PAYMENT", "Awaiting Payment"

    # Cannot cancel the trip automatically.
    CONFIRMED = "CONFIRMED", "Confirmed"
    COMPLETED = "COMPLETED", "Completed"
    PARTIAL_PAYMENT = "PARTIAL_PAYMENT", "Partial Payment"

    CANCELLED = "CANCELLED", "Cancelled"

    @classmethod
    def is_cancelled(cls, status):
        return status == cls.CANCELLED

    @classmethod
    def can_be_cancelled(cls, status):
        return status in (
            cls.PENDING,
            cls.WAITING_PAYMENT,
            cls.CANCELLED,
        )
