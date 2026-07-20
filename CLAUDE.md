# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`django-trips` is a reusable Django app (published as a pip package, see `setup.cfg`) providing a REST API for
managing trips, schedules, bookings, hosts, and locations. It's the core trips service behind the
[DestinationPak](https://destinationpak.com) platform. Consumers install it and mount its URLs under a namespace of
their choosing (see README "Usage").

Note the two similarly-named top-level packages: `django-trips/` (hyphen) is the throwaway Django *project* shell
used only for local dev (`settings.py`-style `urls.py`, `wsgi.py`, `asgi.py`); `django_trips/` (underscore) is the
actual app that gets published and contains all real logic.

## Common commands

All development happens inside Docker; there is no supported bare-metal workflow.

```bash
make build          # docker compose build (destroys existing containers first)
make dev.up          # start web + mysql containers
make shell           # attach a shell inside the web container (django-shell alias)
make update_db        # run migrations
make random_trips      # seed random trips (generate_trips --batch_size=100)
make test            # docker compose run --rm web pytest
make stop / make destroy  # stop / tear down containers (destroy removes volumes too)
make logs            # tail web container logs
```

Running a single test (inside the container, e.g. via `make shell`):

```bash
pytest django_trips/api/tests/test_trip_list.py
pytest django_trips/api/tests/test_trip_list.py::SomeTestCase::test_something
pytest django_trips/management/tests/test_generate_trips.py
```

Test settings use `settings.test` (`DJANGO_SETTINGS_MODULE=settings.test` per `pytest.ini`), which just imports
`settings.common` with `--no-migrations` — tests build schema directly from models, so new migrations aren't
required for tests to pick up model changes (but still create them for real deployments).

Linting:

```bash
python run_lint.py     # pylint over django_trips/, fails if score < 6 (see THRESHOLD in run_lint.py)
```

pep8speaks enforces max line length 120 on PR diffs only (`.pep8speaks.yml`); `.pylintrc` ignores `tests.py`,
`urls.py`, and `migrations` entirely.

## Architecture

### Domain model shape

Everything hangs off `Trip` (`django_trips/models.py`). Key relationships:

- `Trip` → `Host` (organizer) → `HostType`, `HostRating`
- `Trip` → `Location` (via `departure`, `destination` FKs and `locations` M2M) — `Location` is self-referential
  (`parent`) to form a region hierarchy (e.g. a TOWN's parent is a PROVINCE); `Location.region` derives the display
  region from that parent chain, not from a flat field.
- `Trip` → `Category`, `Facility`, `Gear` (M2M lookup-style models, all sharing `ActiveQuerySet`/`is_active`
  filtering via `managers.py`)
- `Trip` → `TripAvailability` (a recurrence rule: DAILY/WEEKLY/MONTHLY/FIX_DATE + a price/seat window) →
  `Trip.create_schedules()` expands a DAILY availability into concrete `TripSchedule` rows (one per bookable date,
  capped at 20 days per call). See the docstring on `create_schedules` for the full expansion flow.
- `TripSchedule` (dated, priced, bookable instance of a trip) → `TripBooking` (a customer's booking against one
  schedule, with an auto-generated `DPT######NN`-style reference number and a `BookingStatus` state machine —
  the allowed transitions are documented in `choices.py` on `BookingStatus`, and `can_be_cancelled`/`is_cancelled`
  are the canonical checks, not ad-hoc string comparisons).
- `Trip.starting_price` is computed as the min price across active-or-upcoming schedules, not stored.
- `TripReview` (an individual, per-trip rating breakdown) is distinct from `TripReviewSummary` (a curated,
  one-to-one *rollup* per trip — not auto-computed from `TripReview` rows) which is in turn distinct from
  `Testimonial` (freeform, site-wide marketing quotes not tied to a specific trip) — don't conflate these when
  adding review-related features. `get_trip_review_summary_data()` in `api/serializers.py` is the shared helper
  (used by both `TripListSerializer` and `TripDetailSerializer`) that renders `TripReviewSummary` as all-zero
  defaults when none has been curated yet, plus a `reviews_count` of verified `TripReview` rows — it's a plain
  function rather than a serializer-mixin field because DRF's `ModelSerializer` silently auto-builds a field from
  the model when a same-named field is declared on a non-`Serializer` base class.
- `CancellationPolicy`/`RefundPolicy` are `ConfigurationModel` (django-config-models) singletons for the
  host-wide default; `Trip.cancellation_policy`/`refund_policy` properties prefer the host's own policy over these
  defaults when set.

### API layer

- `django_trips/api/urls.py` wires a DRF `DefaultRouter` (`TripViewSet`, booking viewset) plus explicit `path()`
  entries for endpoints that don't fit REST-router conventions (upcoming trips, destinations, categories, nested
  booking creation). drf-spectacular serves schema/swagger/redoc from the same urlpatterns.
- `TripViewSet.lookup_field = "identifier"` — trip detail/update/delete accept either a numeric PK or a slug
  (`get_object()` branches on `identifier.isdigit()`). Any new single-trip endpoint should follow this convention.
- Serializer/permission selection is action-based (`get_serializer_class`, permission via
  `IsAuthenticatedOrReadOnly` + `IsStaffForDeleteOnly`): list/retrieve are public, create/update need auth, delete
  needs staff. PATCH is deliberately unsupported (`http_method_names` excludes it).
- Filtering uses `django_filters`, not ad-hoc query param parsing. `TripFilter`/`UpcomingTripsFilter` in
  `api/filters.py` are the pattern to extend. Note `TripFilter.filter_queryset`: price/date filters are
  intentionally *not* independent per-field django-filter fields — they're combined into a single `Q` against
  `TripSchedule` in `filter_queryset()` so a trip only matches if *one* schedule satisfies all constraints together
  (otherwise a trip could match via two different schedules, e.g. a cheap-but-past one and an
  expensive-but-future one). Follow this combined-constraint pattern for any new multi-field schedule filter.
- Ordering uses DRF's `OrderingFilter`, and where ordering is by an annotated/computed value (e.g. `?ordering=price`
  on `TripViewSet.list`), the queryset annotation name must exactly match the ordering field name — DRF orders by
  the literal client-supplied term, not an alias — and must not collide with an existing model property name (see
  the comment above `TripViewSet.ordering_fields`, and `get_queryset()`'s `Min("schedules__price", ...)`
  annotation, both scoped to `status=ScheduleStatus.PUBLISHED`).
- `api/paginators.py` has two active styles plus one unused one: `CustomLimitOffsetPaginator` (limit/offset, used
  by `TripViewSet`/`UpcomingTripsListAPIView`) vs `TripBookingsPagination` (page-number style, default DRF
  envelope, used by the booking list/create views in `api/views/booking.py`). `TripResponsePagination` (a
  page-number paginator with a custom `{next, previous, count, current, pages, results}` envelope) is defined but
  not currently wired to any view — don't assume it's live on an endpoint just because it exists. Match whichever
  style the endpoint you're touching already uses; they are not interchangeable response shapes for existing
  clients.
- Auth is dual: `SessionAuthentication` (browsable API) and JWT (`rest_framework_simplejwt`, 7-day access /
  15-day refresh, see `SIMPLE_JWT` in `settings/common.py`).

### Management commands

`generate_trips` (`django_trips/management/commands/generate_trips.py`) seeds fake trips/hosts/locations for local
dev, driven by the `TRIP_*` settings in `settings/common.py` (`TRIP_DESTINATIONS`, `TRIP_HOSTS`,
`TRIP_LOCATIONS_BY_REGION`, etc.) unless the consuming project sets `USE_DEFAULT_TRIPS=True`. When adding new
seed-relevant settings, update both `settings/common.py` and the README's "Generate random trips" section together.

### Settings

`settings/common.py` is the real settings module (Docker sets `DJANGO_SETTINGS_MODULE=settings.common`);
`settings/test.py` just re-exports it for pytest. `django-trips/wsgi.py`/`asgi.py`/`urls.py` are the minimal dev-only
project shell and aren't part of the published package.
