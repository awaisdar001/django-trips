# Tour Listing Page — Data Model Gap Analysis

Source reviewed: `~/Downloads/Tour Listing.html` (a DestinationPak-branded tour
listing page mockup — the same content also lives, unminified, at
`~/Downloads/Tour listing page design/Tour Listing.dc.html`, which is what the
line references below point into).

This page renders: header/search → "Popular in {destination}" highlight pills →
filter sidebar (start date, duration, price range, trip style) → sort bar →
a list of tour cards (image carousel, title, location, days/people badges,
facility list, trust badges, rating, price, CTA) → "nearby destinations" footer.

## 1. Already fully supported — no gap

| UI element | Backed by |
|---|---|
| Title, destination pin | `Trip.name`, `Trip.destination` → `Location` |
| Duration (days) + min/max duration filter | `Trip.duration` (`DurationField`) + `TripFilter.duration_from/duration_to` |
| Price range filter, "Starting From" price | `TripFilter.price_from/price_to`, `Trip.starting_price` |
| Trip style checkboxes w/ counts | `Category` model + `ActiveCategoriesListAPIView` (already annotates `trips_count`) |
| Sort by price / name / duration | `TripViewSet.ordering_fields` |
| Start date filter | `TripFilter.date_from/date_to` |
| Facilities as a concept (breakfast, transport, guide, hotel stay) | `Facility` M2M on `Trip` already exists |
| Cancellation policy text | `Trip.cancellation_policy` / `CancellationPolicy` |
| "Bestseller / Popular / Top Rated" style badge | `Trip.featured` (`FeaturedType`) |
| Rating score + review count | `TripReviewSummary` + `get_trip_review_summary_data()` |

## 2. Missing data models (need to be created)

### 2.1 Trip photo gallery — **high priority**
Every card shows a 3-photo carousel (dots + prev/next). Today a trip has
exactly one image: `Trip.metadata["poster"]` (a single URL string inside a
JSONField, see `Trip.poster` property, `django_trips/models.py:414`). There is
no way to store, order, or manage multiple photos per trip.

Proposal: new model, e.g.
```python
class TripImage(models.Model):
    trip = models.ForeignKey(Trip, related_name="images", on_delete=models.CASCADE)
    image = models.URLField()  # or ImageField if uploads move server-side
    order = models.PositiveSmallIntegerField(default=0)
    alt_text = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["order"]
```
Keep `metadata["poster"]` as a deprecated fallback, or migrate its value into
the first `TripImage` row. Needs: migration, admin inline on `TripAdmin`,
serializer (`images` on both list/detail serializers).

### 2.2 Wishlist / favorites — **medium priority**
Every card has a heart/favorite toggle. There is currently no model anywhere
in the app for a user saving a trip (`grep -rni "wishlist\|favorite"` across
`django_trips/` returns nothing) — the mockup's heart state is purely local
JS state (`this.state.favs`), not backed by real data.

Proposal:
```python
class TripWishlist(models.Model):
    user = models.ForeignKey(User, related_name="wishlisted_trips", on_delete=models.CASCADE)
    trip = models.ForeignKey(Trip, related_name="wishlisted_by", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "trip")
```
Plus a small toggle endpoint and an `is_wishlisted` field on `TripListSerializer`
(computed from `request.user`, false/omitted for anonymous users).

### 2.3 Location highlights / points of interest — **medium priority**
The "Popular in Hunza Valley" pill row (Attabad Lake, Passu Cones, Khunjerab
Pass, Eagle's Nest, Hopper Glacier — each with its own icon) has no backing
concept at all. `Location` has no relation for curated points of interest.

Two options, pick one:
- **Dedicated model** (recommended — needs per-item icon + manual ordering,
  similar in spirit to `Facility`/`Category`):
  ```python
  class LocationHighlight(models.Model):
      location = models.ForeignKey(Location, related_name="highlights", on_delete=models.CASCADE)
      label = models.CharField(max_length=100)
      icon = models.CharField(max_length=50, blank=True)
      order = models.PositiveSmallIntegerField(default=0)
  ```
- **JSONField on `Location`** — consistent with the existing `travel_tips`
  JSONField pattern, less admin-friendly, no per-row ordering/uniqueness.

### 2.4 Facility / Category icon field — **low-medium priority**
Each facility row renders a specific icon (`coffee`, `bus`, `user-round`,
`bed-double`, …). In the mockup this is hardcoded per-facility in JS. Neither
`Facility` nor `Category` has any field to drive this from real data — adding
a new facility today gives the frontend no way to know which icon to render
without a fragile name-matching lookup table.

Proposal: add `icon = models.CharField(max_length=50, blank=True)` to
`Facility` (and optionally `Category`, since the header nav / trip-style
filters are icon-led too).

## 3. Existing models are fine, but the API doesn't expose them yet (serializer/endpoint gaps, not model gaps)

- **`TripListSerializer` is missing `facilities` and `passenger_limit_min`/`passenger_limit_max`.**
  The card needs both (facility rows, "From 2 to 50 people"), but today those
  fields only exist on `TripDetailSerializer` (`django_trips/api/serializers.py:367`
  vs `:448`/`:453`). Fix is additive: add `facilities = FacilitySerializer(many=True)`
  and the two passenger fields to `TripListSerializer`.
- **No "nearby destinations" endpoint.** The footer ("That's all N tours in
  Hunza Valley — explore Skardu, Naran Kaghan, Swat Valley…") is achievable
  with the existing `Location.parent` self-reference (siblings under the same
  parent), but nothing currently queries/exposes it.
- **No sort-by-rating.** "Sort by → Rating" has no backing annotation.
  `TripViewSet` already annotates `price` onto the queryset for `?ordering=price`
  (`django_trips/api/views/trip.py:91`) — sorting by rating needs the same
  treatment: annotate the `TripReviewSummary.overall` value (or a computed
  Avg of `TripReview.overall`) onto the queryset and add it to `ordering_fields`.
- **No numeric/rating-word mapping.** The card shows a word label ("Superb",
  "Excellent", "Very Good") next to the numeric score. This doesn't need a
  new model — just a small score→word lookup helper (similar to
  `format_trip_duration` in `utils.py`) surfaced through the review-summary
  serializer output.

## 4. Design assumes data shapes that don't exist yet (needs a product decision)

- **"Trust badges"** (PTDC registered, Free cancellation 48h, Licensed guide):
  only `Host.verified` (a plain boolean) and `Trip.cancellation_policy` (a
  freeform paragraph, e.g. *"80% refunded if canceled 21+ days before…"*)
  exist. The design assumes short, structured, badge-sized facts — a numeric
  cancellation window, not a paragraph. Real "Free cancellation 48h" would
  need a structured field (e.g. `free_cancellation_hours` on
  `CancellationPolicy`/`Host`); "PTDC registered" / "Licensed guide" have no
  backing field at all today (could be `Host.license_number` +
  `certifying_body`, or may just be static marketing copy gated on
  `Host.verified` — needs a call from product before modeling it).
- **Currency.** The mockup takes `currency` as a page-level prop (PKR/USD) and
  shows a footer "Currency: PKR" selector, but nothing in `settings/common.py`
  or the models represents currency — pricing is an unqualified
  `DecimalField` and `Trip.country` defaults to `"PK"`. If multi-currency
  display is a real near-term requirement, that's a meaningfully bigger scope
  (FX rates, per-schedule currency) than this page; otherwise the currency
  string is just static UI copy and not a data gap.
- **"Recommended" sort** has no real ranking signal — it silently falls back
  to `Trip`'s default ordering (`-created_at, -id`). Fine as a placeholder,
  but flagging in case "recommended" is meant to encode real ranking logic
  (e.g. featured trips first, then rating) later.

## 5. Unrelated bug spotted while reading `models.py`

`Trip.create_schedules()` (`django_trips/models.py:530`) calls:
```python
TripSchedule.objects.get_or_create(trip=self, date_from=schedule_date, ...)
```
but `TripSchedule` has no `date_from` field — only `start_date`/`end_date`.
This looks like a leftover from a prior rename and would raise at call time.
Circumstantial evidence: `django_trips/tests/test_models.py:230` has a test
named `stest_trip_availability` (note the `s` prefix — not collected by
pytest, i.e. effectively disabled) that uses the same stale `date_from=`
kwarg. Not part of this page's data needs, but worth a follow-up ticket since
it means `create_schedules()` is currently untested and likely broken.

## Suggested order of work

1. `TripListSerializer` additions (facilities, passenger limits) — no schema
   change, immediate card-completeness win.
2. `TripImage` model + migration + admin + serializer — unblocks the carousel,
   the single biggest visual gap.
3. `Facility.icon` (+ `Category.icon` if the icon-led nav pills are wanted) —
   small schema change, removes a frontend hardcoded lookup table.
4. `TripWishlist` model + toggle endpoint + `is_wishlisted` field.
5. `LocationHighlight` model (or JSONField, per product's call) + "Popular in
   {destination}" endpoint/serializer field.
6. Nearby-destinations lookup + rating-based ordering annotation.
7. Product decision on trust badges / currency scope, then model accordingly.
8. File a separate follow-up for the `create_schedules()` / `date_from` bug.
