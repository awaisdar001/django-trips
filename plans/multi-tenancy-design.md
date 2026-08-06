# Multi-tenancy & the three-surface architecture

Status: **proposed** — decisions in §2 are settled; §12 lists what still needs a call.
Supersedes the first draft (which put the management API in the lib).

---

## 1. What we're building

Independent tour operators sign up, log in, and manage their own trips and bookings from a
dashboard. Their trips appear in one shared public catalog that anyone can browse and book
from — logged in or not. Travellers who do log in get a profile area for their own bookings,
favourites, and subscription settings.

That's **three distinct surfaces**, and they differ in the one thing that matters most here —
how rows are scoped:

| # | Surface | Who | Scoping model | Auth |
|---|---|---|---|---|
| **A** | Operator dashboard | Host members | **Tenant-scoped** — rows belong to a `Host` | Required |
| **B** | Public app | Anyone | **Unscoped** — full catalog | Optional |
| **C** | Traveller profile | Any logged-in user | **Self-scoped** — rows belong to a `User` | Required |

This is a marketplace, not classic SaaS multi-tenancy: tenants share a database and share the
public read surface. No schema-per-tenant, no per-tenant database, no subdomain routing. The
homepage is by definition a cross-tenant read.

### 1.1 The distinction that will cause bugs if ignored

**Tenant-scoping and self-scoping are different mechanisms, and `TripBooking` is reachable
through all three surfaces:**

- Surface A — an operator sees bookings where `schedule__trip__host` is their host
- Surface B — a guest looks up a booking by `number` + `email`
- Surface C — a traveller sees bookings where `created_by` is them

Same model, three different scoping rules. **Never write one viewset that branches on the
requesting user's type** — that branch is where the leak will eventually appear. Three
surfaces means three viewsets over the same model, each with one unconditional scoping rule.

A user can be both an operator and a traveller (operators book other people's trips). So
"role" is not a field on the user — it's the question *"does this user have any host
memberships?"*, answered per-request.

---

## 2. Settled decisions

| # | Decision |
|---|---|
| 1 | `Host` is the tenant boundary |
| 2 | **`django-trips` owns models, schema, serializers, and services only — it is tenancy-oblivious. It ships no management views, no auth endpoints, and no tenancy/scoping logic.** |
| 3 | **`destipak` owns all management endpoints, all token/session logic, both dashboards, all tenancy/scoping logic (membership, resolver, host-aware permission classes), and all policy** |
| 4 | Concrete `HostMembership`, the host-resolver, and tenant-scoping helpers all live in destipak — not a pluggable hook shipped by the lib |
| 5 | The lib keeps the **public** catalog/booking API (surface B) — it's already there and is domain, not application, logic |
| 6 | No backwards-compatibility shims, and no generic pluggable-settings extension points (dotted-path resolvers, `DEFAULTS`/`import_string`-style indirection) — we own both repos and there is exactly one consumer, so lib code that needs configuring imports destipak directly or takes a plain constant, not a settings-driven hook aimed at an audience that doesn't exist |

### 2.1 The seam, stated precisely

**django-trips = domain library, with zero tenancy awareness.** Models, migrations, plain
managers/querysets, serializers, business services (`services.py`, `create_schedules`, pricing,
booking state machine), and the public read/booking API. It has no concept of `Host`
membership, no scoped querysets, and no host-aware permission classes. `Host` itself stays a
plain domain model (the organizer a `Trip` belongs to) — that doesn't change; only the
*membership/authorization* layer on top of it moves out.

*(Revised after Phase 4.1 landed: `IsStaffForDeleteOnly` is gone, not kept. It was a domain rule
in theory, but its only real consumer was `TripViewSet`'s `destroy` action — once that action was
dropped (§9.1), the class had zero callers in either repo, so it was dead code, not a kept
seam-piece. If an operator-facing "staff can force-delete" rule turns out to be needed later, it
belongs in destipak next to the other host-aware permission classes (§6.5), not resurrected here —
Phase 4A's design (§9.2) doesn't currently call for one.)*

**destipak = application, and the tenancy layer.** Login/registration/tokens, the operator
management API, the traveller profile API, URL routing and exposure decisions, both React
surfaces, operator verification workflow, commissions, branding — plus `HostMembership`, the
host-resolver, tenant-scoping helpers, and host-aware permission classes (all §6).

Rule of thumb: **if it needs to know what a session, a token, or "who's allowed to manage this
host" is, it belongs in destipak. If it only needs to know what a `Trip` is, it belongs in the
lib.** Tenancy is squarely the first kind — it's an authorization concept, not a domain one, so
it was always a layering mismatch for the lib to own it.

### 2.2 An honest cost of this split

Management viewsets move to destipak, but **serializers should not**. `TripCreateSerializer`
already exists in the lib and handles a genuinely complex model — `Trip` has five M2Ms
(`locations`, `categories`, `facilities`, `gear`, `trust_badges`), nested itineraries,
packages, and images. Rewriting that in destipak would be a large duplication for no benefit,
and would leave two definitions of "a valid trip" to drift apart.

So: **destipak imports serializers and plain (unscoped) querysets from the lib, applies its own
scoping on top (§6.3/§6.4), and writes only the viewsets, URLs, and permissions around them.**
The lib stays a library; destipak stays thin.
If a serializer needs a request-specific behaviour, pass it through serializer context rather
than forking the serializer.

---

## 3. Where things stand today (verified)

Worth stating plainly, because it changes the sequencing:

- **The React app is not live.** It's mounted at `^react-demo/` (`djangoapps/public/urls.py:36`)
  as a `TemplateView` catch-all over `templates/marketing/react-demo.html`. The real site is
  still legacy Django templates.
- **Single fixed bundle, no code splitting.** `frontend/vite.config.ts` pins
  `rollupOptions.input: 'src/main.tsx'` with `entryFileNames: 'main.js'` and
  `autoCodeSplitting: false` (deliberately — per-route chunks would collide under one
  filename). Anything added to this entry ships to every public visitor.
- **Auth is session cookies, not JWT.** `frontend/src/api/client.ts` uses
  `withCredentials: true` plus a `csrftoken` → `X-CSRFToken` interceptor. The JWT endpoints in
  `django_trips/urls.py` exist but the frontend doesn't use them.
- **`AUTH_USER_MODEL` is now a real custom model, not a proxy hack.** `destipak` swapped in
  `accounts.User` (`djangoapps/accounts/`, reusing the pre-existing `auth_user` table via
  `Meta.db_table`, zero data migration) in place of the old `public.MyUser` proxy, which needed
  `destiPak.middleware.DestinationPakMiddleware` to swap `request.user`'s class on every
  request. That middleware is deleted. This makes §5 (Phase 0) testable against a real swap
  instead of a hypothetical one — and re-verifying it against this project found the original
  framing overstated the problem in one place and understated it in another; see §5 for the
  corrected picture.
- **There is no registration flow.** Only `login_view` (`djangoapps/public/views/user.py:70`,
  rendering `new/login.html`, routed at `djangoapps/public/urls.py:123`) and `admin_login`.
  Signup has to be built from scratch.
- **`Subscriber` (`djangoapps/public/models.py:1590`) is email-only** — `uuid`, `email`,
  `active`, `created_at`, with no FK to `User`. "Subscription settings on the profile page"
  therefore needs a link built, not just a page.
- **`Trip` has no draft/publish state** — only `is_active` (`models.py:448`), which is used
  for soft-delete/visibility, not editorial workflow.

---

## 4. Pre-existing security bug (fix first, independently)

`TripBookingRetrieveUpdateViewSet` (`django_trips/api/views/booking.py:35-39`) sets
`queryset = TripBooking.objects.all()` with `permission_classes = [IsAuthenticated]` and
`lookup_field = "number"`, and never overrides `get_queryset()`. **Any authenticated user can
read, update, or cancel any booking** given its reference number — including via the `cancel`
action (line 84).

The anonymous `TripBookingLookupView` (line 126) is correctly scoped (requires `number` AND
`email`). The authenticated path being weaker than the anonymous one is backwards.

Fix this on its own branch now. Don't let it wait on a ten-phase rollout.

---

## 5. Phase 0 — portability prerequisites (lib)

Originally written as "the lib can't currently be installed by a project with a custom user
model" — now that destipak actually has one (§3), that claim is checkable, and it turns out to
be **too strong**. `django_trips` *is* installed against `AUTH_USER_MODEL = "accounts.User"`
right now, `manage.py check` is clean, and trip pages serve correctly. The real remaining work
splits into two very different severities — don't treat them as one bucket.

(Worth a note since §6 below reassigns tenancy ownership: this phase isn't about tenancy at all
— it's about the lib correctly deferring to *whatever* `AUTH_USER_MODEL` a consuming project
sets for its own plain FKs like `Trip.created_by`. It stays lib-side regardless of who owns
`HostMembership`.)

### 5.1 Not currently broken, but not portable by design — fix opportunistically

`django_trips/models.py:31` — `User = get_user_model()` at import time, then used directly as a
relation target, e.g. `Trip.created_by = models.ForeignKey(User, ...)` (`models.py:452`).

- **Why it isn't broken today:** `get_user_model()` is called with `require_ready=False`
  internally, which lazily imports the target app's models on demand instead of requiring strict
  `INSTALLED_APPS` order — and `djangoapps.accounts` (loaded *after* `django_trips` in
  `destiPak/settings/base.py`) doesn't import anything from `django_trips`, so there's no
  circular import to trigger it. It's also migration-neutral: Django's autodetector
  special-cases any FK target whose `_meta.swappable` is set and always serializes it as
  `to=settings.AUTH_USER_MODEL`, regardless of whether the source passed the string or a
  resolved class — confirmed `django_trips/migrations/0001_initial.py:217` already reads
  `to=settings.AUTH_USER_MODEL`.
- **Why it's still worth fixing:** it works *by luck of this project's current app order and
  import graph*, not by contract. A different consuming project whose custom-user app imports
  anything — even transitively — from `django_trips` before its own models finish registering
  hits `AppRegistryNotReady` or a circular import at server start. Swap
  `User = get_user_model()` for the `settings.AUTH_USER_MODEL` string in FK/M2M `to=` params,
  which matches what the migration file already independently settled on.

### 5.2 Actually broken today — not hypothetical, fix before anything else in this phase

Two places still import the **concrete, swapped-out** `django.contrib.auth.models.User`
directly instead of resolving through `AUTH_USER_MODEL`. That class has no backing table in
destipak anymore (`accounts.User` claimed the `auth_user` table; the migration executor skips
`auth.0001_initial`'s `CreateModel` for `User` because it's swapped) — this is not a portability
nicety, it's the wrong model in the actually-running app:

1. `django_trips/api/serializers.py:6` (`from django.contrib.auth.models import User`) /
   `:49` (`UserSerializer.Meta.model = User`). It doesn't currently 500 only because
   `accounts.User` and the swapped-out `auth.User` both extend `AbstractUser`, and this
   serializer's `fields` (`username`, `full_name`, `first_name`, `last_name`) happen to be
   attributes both classes share — that's coincidence, not correctness. Confirmed this is live
   and exercised, not dead code: it's nested as `TripDetailSerializer.created_by`
   (`serializers.py:806`), which renders on the **public, unauthenticated** trip-detail endpoint
   (surface B). The moment `accounts.User` diverges from stock `AbstractUser` (a new field, an
   overridden `get_full_name()`), or drf-spectacular introspects `Meta.model` for schema
   generation, this silently serializes/documents the wrong model. Fix: resolve `User` via
   `django.contrib.auth.get_user_model()` in this module instead of the concrete import.
2. `django_trips/tests/factories.py:11` (`from django.contrib.auth.models import Group, User`)
   / `:80` (`UserFactory.Meta.model = User`). Any test using this factory creates rows against
   the swapped-out, tableless class — a real risk for any downstream consumer's test suite.
   (destipak's own tests don't hit this: `djangoapps/public/tests/lib.py` has its own
   `UserFactory` targeting `accounts.User` directly.) Fix inside the factory the same way.

That's the whole phase — two items, both lib-side. An earlier draft had a third: a
`django_trips/conf.py` settings-indirection layer (`DEFAULTS` dict + `import_string`, DRF/allauth
style) for a pluggable host-resolver. Dropped outright, not just moved — see §2 decision 6:
there's one consumer, so it's a direct function call (§6.2), not a settings hook.

---

## 6. Phase 1 — tenancy primitives (destipak, no lib changes)

Originally scoped as lib-side — `HostMembership` shipped by `django_trips`, with a pluggable
resolver hook for consumers to override. That's reversed per §2 decision 6:
**`django_trips` stays tenancy-oblivious end to end.** It never imports a `Host`-membership
concept and ships no scoping code. Everything below lives in a new destipak app instead (name
TBD, §13.2) and imports the lib's plain models (`Trip`, `TripSchedule`, `TripBooking`, `Host`,
...) the way any other destipak app would — no hook needed on the lib side, because there's
exactly one implementation and one caller, both in destipak.

One concrete consequence: **Phase 1 is a single-repo phase now.** Unlike Phase 0 (§5) and the
surface-B hardening in Phase 4A (§9.1), landing it needs no `django_trips` PR at all — see §16.

### 6.1 Membership model

```python
# djangoapps/<hosts>/models.py  (destipak — app name per §13.2)
from django.conf import settings
from django.db import models
from django_extensions.db.models import TimeStampedModel

from django_trips.models import Host


class HostRole(models.TextChoices):
    OWNER = "OWNER", "Owner"
    MANAGER = "MANAGER", "Manager"
    STAFF = "STAFF", "Staff"


class HostMembership(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="host_memberships",
                             on_delete=models.CASCADE)
    host = models.ForeignKey(Host, related_name="memberships", on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=HostRole.choices, default=HostRole.OWNER)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("user", "host")
```

`HostRole` is destipak's own choices class now — the original draft had it join
`BookingStatus` in the lib's `choices.py`, which only made sense while `HostMembership` itself
lived in the lib. Ship the column now, enforce only membership initially — the column is free,
the permission matrix isn't.

Deliberately **no** login or billing fields on `Host` (still a lib model, unchanged by this
split — see §1). `Host` stays the public brand profile (name, description, `HostType`, ratings —
all rendered on trip cards today); `HostMembership` is the account seam, and it's an entirely
ordinary cross-app FK from a destipak model into a lib model — no different from any other app
that has a foreign key into `django_trips.models`. One account running two brands later needs no
migration.

### 6.2 Resolver

```python
# djangoapps/<hosts>/tenancy.py  (destipak)
from django_trips.models import Host

from .models import HostMembership


def get_manageable_hosts(user):
    """Return the Host queryset this user may manage."""
    if not user or not user.is_authenticated:
        return Host.objects.none()
    return Host.objects.filter(memberships__user=user, memberships__is_active=True)


def is_platform_staff(user):
    return bool(user and user.is_authenticated and user.is_staff)
```

Every scoping decision goes through `get_manageable_hosts()`; nothing queries `HostMembership`
directly outside this module — that chokepoint is the whole value of this design, and it's a
plain function precisely because §2 decision 6 rules out building it as a settings-driven hook
for consumers that don't exist. `is_platform_staff` can still be narrowed to a specific group
later without touching call sites — that's a one-line change inside this function, no
indirection layer required to make it possible.

### 6.3 Tenant scoping — composition, not queryset mixins

The original draft added a `HostScopedQuerySet` mixin as a second base class onto the lib's own
`TripQuerySet`/`TripScheduleQuerySet`/`TripBookingManager`. That option is gone — the lib
doesn't accept scoping-aware base classes, since that's exactly the tenancy awareness §2 now
rules out. Instead, destipak scopes the lib's plain querysets **from the outside**, via a lookup
table plus a filter helper it owns entirely:

| Model | `host_lookup` |
|---|---|
| `Trip` | `host` |
| `TripSchedule`, `TripAvailability`, `TripPackage` | `trip__host` |
| `TripImage`, `TripItinerary`, `TripPickupLocation` | `trip__host` |
| `TripBooking` | `schedule__trip__host` |

```python
# djangoapps/<hosts>/tenancy.py  (destipak, continued)
from django_trips.models import (
    Trip, TripAvailability, TripBooking, TripImage,
    TripItinerary, TripPackage, TripPickupLocation, TripSchedule,
)

HOST_LOOKUP = {
    Trip: "host",
    TripSchedule: "trip__host",
    TripAvailability: "trip__host",
    TripPackage: "trip__host",
    TripImage: "trip__host",
    TripItinerary: "trip__host",
    TripPickupLocation: "trip__host",
    TripBooking: "schedule__trip__host",
}


def for_host_member(queryset, user):
    if is_platform_staff(user):
        return queryset
    host_lookup = HOST_LOOKUP[queryset.model]
    return queryset.filter(**{f"{host_lookup}__in": get_manageable_hosts(user)})
```

Every operator-surface viewset's `get_queryset()` calls
`tenancy.for_host_member(Trip.objects.all(), request.user)` (or whichever lib model) rather than
a `.for_host_member()` method on the queryset itself — the lookup table is still the one place
that has to know the FK path per model, same as before; it's just owned by destipak instead of
the lib.

### 6.4 Self-scoping (for surface C) — same composition pattern

```python
# djangoapps/<hosts>/tenancy.py  (destipak, continued)
def for_customer(queryset, user):
    return queryset.filter(created_by=user)
```

Two differently-named functions, never one with a mode flag — same reasoning as the original
draft, just as plain functions instead of queryset methods. A reviewer reading a viewset can
still tell which surface it serves from the call alone (`tenancy.for_host_member(...)` vs.
`tenancy.for_customer(...)`).

### 6.5 Permission classes — destipak, not the lib

`IsHostMember` and `IsHostMemberOfObject` move to `djangoapps/<hosts>/permissions.py`
(destipak) — both need `get_manageable_hosts()`, which is destipak-only now. (Originally this
section also said the lib keeps `IsStaffForDeleteOnly` as a domain rule — Phase 4.1 found its only
caller was the very `destroy` action §9.1 removes, so it had no reason to survive; see §2.1's note.
If an operator-side "staff can force-delete" rule turns out to be needed, it's a new destipak class
here, not that one revived.)

**Cross-tenant access must still return 404, not 403** — a 403 confirms the object exists and
leaks a competitor's catalog shape. Scoping in `get_queryset()` (via `tenancy.for_host_member`)
gives 404 for free; that's still the main reason to scope there rather than in
`has_object_permission`.

---

## 7. Phase 2 — auth moves to destipak

1. **Remove the token endpoints from the lib.** `django_trips/urls.py` currently mounts
   `TokenObtainPairView` at `api/token/` and `TokenRefreshView` at `api/token/refresh/`. A
   domain library shouldn't own auth. Move to destipak's URLconf; `SIMPLE_JWT` config already
   lives in `destiPak/settings/trips.py:10-15`.
2. **Keep session cookies as the primary browser mechanism.** The React app is served
   same-origin by Django and `client.ts` already does session + CSRF correctly. Session cookies
   are `httpOnly` and immune to XSS token theft; localStorage JWTs aren't. Retain JWT strictly
   for future machine-to-machine clients, not for the dashboard.
3. **Build registration.** Nothing exists today. Needs: signup, email verification, password
   reset, and a decision on whether traveller signup and operator signup are one flow with a
   later upgrade, or two front doors (see §12).

---

## 8. Phase 3 — identity endpoint (destipak)

The frontend can't decide where to land a user without asking. One endpoint underpins all
routing:

```
GET /api/me/
{
  "id": 42,
  "email": "...",
  "display_name": "...",
  "hosts": [ {"id": 7, "slug": "karakoram-treks", "name": "...", "role": "OWNER",
              "verified": true} ],
  "is_staff": false
}
```

- `hosts: []` → traveller. Public app + `/account`. No dashboard nav.
- `hosts: [...]` → also an operator. Dashboard nav appears; they keep full traveller access.
- Anonymous → 401, public app only.

Return the **whole** membership list, not a boolean. Multi-host operators exist eventually and
retrofitting a host-switcher onto a boolean is painful.

---

## 9. Phase 4 — the three API surfaces

### 9.1 Surface B — public (stays in the lib, hardened) — ✅ done

Keeps its current home in `django_trips/api/`. Changes:

- `TripViewSet` (`api/views/trip.py:56`) drops `create`/`update`/`destroy` — base class changed
  from `ModelViewSet` to `ReadOnlyModelViewSet`, which also means `create`/`update`/`destroy`
  are unreachable at the URL-binding level, not just permission-denied: `SimpleRouter`'s
  `get_method_map()` only binds a verb to a route when `hasattr(viewset, action)`, so once those
  mixins are gone the router never wires `post`/`put`/`delete` to `/trips/` or `/trips/<id>/` in
  the first place. `get_serializer_class()`'s `create`/`update` branch (and the `TripCreateSerializer`
  import) dropped accordingly — the serializer itself stays in the module for destipak to import
  later (§2.2), just unused by this viewset now. The now-unused `IsStaffForDeleteOnly` goes away
  (see §2.1's note — deleted, not kept).
  - **Gotcha found during implementation:** `http_method_names` could **not** narrow to `["get"]`
    alone — it's checked once by Django's base `View.dispatch()`, class-wide, before DRF resolves
    which action a request maps to. The `wishlist` extra action (`@action(detail=True,
    methods=["post"], url_path="wishlist")`) is POST, so a bare `["get"]` 405'd the wishlist
    toggle too. Landed as `["get", "post"]` instead — `post` stays reachable only for `wishlist`,
    since the router-level `hasattr()` filtering above already keeps `create` unreachable
    regardless of what's in `http_method_names`.
  - **Test fallout:** `test_trip_create.py`/`test_trip_update.py`/`test_trip_delete.py` (~30
    tests) exercised `TripCreateSerializer`'s validation logic (itinerary nesting, gear/facility/
    trust-badge handling) through this viewset's create/update actions. Per the redirect in this
    phase's chat (serializer reuse vs. destipak writing its own view — decide at Phase 4A, don't
    over-invest now), these were deleted rather than rewritten to call the serializer directly.
    Replaced with `test_trip_write_methods_disabled.py` (3 tests: POST/PUT/DELETE all 405).
    **Known gap:** `TripCreateSerializer`'s validation logic has no test coverage until Phase 4A
    builds the operator viewset and either reuses this serializer (bring the deleted tests back,
    adapted to call it directly) or writes its own.
- `TripBookingCreateView` (`booking.py:116`) stays `AllowAny` — guest booking is a product
  requirement.
- `TripBookingLookupView` (`booking.py:126`) unchanged; already correctly scoped.
- Everything else (destinations, categories, hosts, trust badges, testimonials, reviews) is
  already public and read-only.
- **Public reads must never be tenant-scoped.** Lock this in with tests (§11) — over-scoping
  the catalog is the regression that empties the homepage.

**Verification:** full suite 327 passed / 1 skipped (342 minus ~30 deleted create/update/delete
tests plus 3 new write-disabled tests, minus one now-moot `get_serializer_class` edge-case test),
`manage.py check` clean, `makemigrations --check --dry-run` no changes, pylint 9.91/10.

### 9.2 Surface A — operator management (new destipak app)

New app, e.g. `djangoapps/hosts/` (or `operator_portal/`), containing viewsets, URLs,
permissions, and the tenancy primitives from §6 (`HostMembership`, the resolver, the scoping
helpers) — serializers and plain (unscoped) querysets imported from the lib, with destipak
applying scoping on top.

| Resource | Operations |
|---|---|
| Trips | list/create/retrieve/update/archive — own host only |
| Schedules & availability | CRUD, plus `create_schedules()` expansion |
| Packages, itineraries, images, pickup locations | CRUD |
| Bookings | list/detail, status transitions, cancel — own trips only |
| Host profile | edit name, description, policies, refund schedule |
| Team | invite/remove members (Phase 2 of dashboard; needs `HostRole` enforcement) |

Every viewset: `permission_classes = [IsAuthenticated, IsHostMember]` (both destipak-local, §6.5)
and a `get_queryset()` that calls `tenancy.for_host_member(<Model>.objects.all(), request.user)`
(§6.3) unconditionally. `host` is assigned server-side on create from the user's membership —
**a client-supplied `host` in the POST body must be rejected**, or the payload is a tenancy
bypass.

### 9.3 Surface C — traveller profile (destipak)

Lives with the existing user code (`djangoapps/public/`), not with the operator app — the
distinction is worth keeping visible in the directory structure.

| Resource | Backing |
|---|---|
| My bookings | `tenancy.for_customer(TripBooking.objects.all(), user)` (§6.4) |
| My favourites | `TripWishlist` (already exists; toggle endpoint already in the lib) |
| Profile details | `UserProfile` (`djangoapps/public/models.py:1003`) |
| Subscription settings | `Subscriber` (`models.py:1590`) — **needs a `User` link built** |
| My reviews | `TripReview` filtered by user |

Two gaps to close here:

- **`Subscriber` has no `User` FK** — only a unique `email`. Either add a nullable FK and
  backfill by email match, or resolve by email at read time. The FK is cleaner; email is
  mutable and matching on it will drift.
- **Guest bookings have `created_by = null`** (`models.py:1079`). A guest who books and later
  registers with the same email sees an empty bookings list. Needs a claim step: on
  registration (or email verification), attach `TripBooking` rows with a matching, verified
  email. **Only on verified email** — otherwise registering with someone else's address hands
  you their booking history.

---

## 10. Phase 5 — frontend

### 10.1 Bundle strategy

`vite.config.ts` currently emits a single fixed `main.js` from one entry with
`autoCodeSplitting: false`. Adding the dashboard to that entry ships operator code to every
anonymous visitor.

**Recommendation: a second Vite entry.** Change `rollupOptions.input` to an object
(`{main: 'src/main.tsx', dashboard: 'src/dashboard-main.tsx'}`) with matching
`entryFileNames`, emitting `static/react/dashboard.js`. Django serves it from a separate
`login_required` template view at `/host/`. Benefits: zero public bundle growth, a hard
separation between operator and public code, and independent deploy of each. Cost: shared
components need to be importable from both — they currently sit under
`frontend/src/app/shared/components`, which is inside the public route tree and should move up
a level if two entries are going to share them.

Note `src/booking-lookup-main.tsx` already exists as a second entry, with a full page tree
under `src/booking-lookup/` — but it is *not* wired into `rollupOptions.input`, so it isn't
being built. Resolve its status first; it's either the precedent for multi-entry or dead code,
and which one it is changes how much work §10.1 actually is.

### 10.2 Route structure

```
main.tsx        →  /            public home
                   /trips, /trips/$slug
                   /account/bookings | /favourites | /settings   (auth-gated)
dashboard.tsx   →  /host/                      dashboard home
                   /host/trips, /host/trips/$id/edit
                   /host/schedules, /host/bookings, /host/profile
```

Auth gating goes in TanStack Router `beforeLoad` against the `/api/me/` query, redirecting to
login with a `?next=`. Server-side, the Django template view for `/host/` is `login_required`
too — **client-side route guards are UX, not security**; every dashboard endpoint enforces
`IsHostMember` independently.

### 10.3 Data layer

Per repo convention: all fetching through TanStack Query hooks in `frontend/src/api/hooks.ts`,
never raw `useState`/`useEffect`; axios confined to `client.ts`. The dashboard needs its own
`baseURL` (destipak's management API, not `/trips/api/v1`) — either a second axios instance or
a `baseURL` parameter on the existing one.

### 10.4 Promotion from `/react-demo/`

Independently of tenancy, the React app has to graduate from `^react-demo/` to real URLs.
Sequence this deliberately: the dashboard can launch at `/host/` **without** the public app
being promoted first, since they're separate entries. Doing so avoids coupling operator
onboarding to a public-site cutover.

---

## 11. Phase 6 — onboarding, verification, data migration

### Onboarding

1. Operator signup → one transaction creating `User` + `Host` + `HostMembership(OWNER)`,
   `Host.verified = False`.
2. Staff review in `stafftools` → flip `verified`.
3. `HostManager.active()` (`managers.py:32-34`) already filters `verified=True`, so unverified
   hosts are excluded from the public hosts list for free. **Confirm the same holds for their
   trips** — otherwise an unverified host's trips list publicly under an invisible host.
4. **Draft trips before verification** — recommended yes; it lets operators build their catalog
   while awaiting approval, which materially improves onboarding conversion. Requires a
   publish/draft state on `Trip` distinct from `is_active` (§3). Decide in Phase 1, not later —
   retrofitting a state field after operators are live means a data migration over real rows.

### Data migration

Existing `Host` rows have no owner, and `Trip.created_by` (`models.py:452`) is unrelated to
`Trip.host` (line 454) — seeded trips were created by staff, not operators.

- Management command `backfill_host_memberships` lives in destipak, not the lib —
  `HostMembership` lives there now (§6.1). Still **not** a data migration, for the same reason
  as before: it encodes destipak's specific data situation (which hosts get a service account
  vs. a real operator), and that has no business in anyone's migration history.
- Per host: attach a real operator account, or a platform-owned service account.
- **Tenancy checks key off `host`, never `created_by`.** These disagree for all seeded data.

---

## 12. Phase 7 — verification

`settings/test.py` runs `--no-migrations`, so model changes are picked up in tests without new
migrations (still required for deploy).

- **`TenantIsolationTestMixin`** — for every operator endpoint, assert host A gets **404, not
  403** on host B's object, across GET/PUT/DELETE.
- **Public-surface tests** — assert catalog endpoints stay unscoped for anonymous users *and*
  for logged-in operators. Over-scoping is as damaging as under-scoping.
- **Cross-surface booking matrix** — the highest-value suite. One booking, four actors
  (its customer, another traveller, its operator, another operator), three surfaces. Assert the
  full grid.
- Client-supplied `host` in a create payload is rejected.
- Booking IDOR regression test (§4).
- Guest-booking claim only fires on verified email.

---

## 13. Decisions still needed

1. **One signup flow or two?** Single traveller signup with a later "become a host" upgrade, or
   separate front doors. The upgrade path is better product (operators are often travellers
   first) but needs the `/api/me/` role model to handle transition.
2. **New destipak app name** — `hosts`, `operator_portal`, or fold into `stafftools`. Recommend
   a new app; `stafftools` is platform-staff tooling and conflating the two invites permission
   mistakes. This app now owns more than viewsets — `HostMembership`, the resolver, and the
   scoping helpers (§6) live here too, which pushes further against folding it into
   `stafftools`.
3. **`Subscriber` link** — nullable `User` FK (recommended) vs email resolution at read time.
4. **Draft/publish state on `Trip`** — needed for §11 point 4. This is a plain `Trip` field
   (lib-side), unrelated to §6's tenancy work despite the similar name — decide and land it
   before Phase 6, not "in Phase 1" (that pointed at the wrong section after §6 was rescoped to
   tenancy-only). Bundling it with Phase 0 is the cheapest slot, since both are lib-side and
   early.
5. **Booking status transitions an operator may perform** — confirm/reject/reschedule? The
   `BookingStatus` state machine in `choices.py` currently encodes customer-side cancellation;
   operator-side transitions may not all exist yet.

---

## 14. Risks

| Risk | Mitigation |
|---|---|
| Booking data leaking across operators | Highest severity. Separate viewsets per surface + the cross-surface matrix test |
| Over-scoping the public catalog (empty homepage) | Public viewsets never import scoping helpers; explicit anonymous-read tests |
| Client-supplied `host` in create payloads | Server assigns from membership; reject mismatches |
| Guest-booking claim hijacking | Claim only on *verified* email |
| Dashboard code inflating the public bundle | Separate Vite entry, not lazy routes (code splitting is off by design) |
| Serializer drift between lib and destipak | destipak imports lib serializers; adds no parallel definitions |
| `/react-demo/` promotion tangled with dashboard launch | Separate entries make these independent — keep them that way |
| Tenancy logic drifting back into the lib | `HostMembership`/resolver/scoping/permissions stay in destipak only (§6); the lib must never gain a scoping-aware queryset or a `Host`-membership FK for this split to hold |

---

## 15. Sequencing

```
Phase 0 (lib portability)  ─┬─→ Phase 1 (tenancy primitives, destipak)
                            │
[SECURITY] booking IDOR ────┘        ↓
                                Phase 2 (auth → destipak)  →  Phase 3 (/api/me/)
                                     ↓                              ↓
                          Phase 4A (operator API)  ←────────────────┤
                          Phase 4C (profile API)   ←────────────────┘
                                     ↓
                          Phase 5 (frontend: dashboard entry, /account routes)
                                     ↓
                          Phase 6 (onboarding, verification, backfill)
                                     ↓
                          Phase 7 (isolation test suite)
```

The booking IDOR fix is independent of everything and should ship first. Phase 4A and 4C are
parallelisable once Phase 3 lands. On closer look, Phase 1 has **no hard dependency on Phase 0**
— `HostMembership` FKs into `Host` and `settings.AUTH_USER_MODEL`, neither of which Phase 0
touches (Phase 0 is entirely about `django_trips`'s own internal `User` handling). It only needs
whatever `django_trips` version is already installed, since that's all it imports `Host` from.
Landing Phase 0 first is still good sequencing — two of its three items are live bugs, not
future-proofing — just not a blocker. See §17 for the full task ordering.

## 16. Branching

`staging` is the base branch in both repos — feature branches off `staging`, PR back into it,
never commit directly. This work spans two repos; land it as paired PRs per phase rather than
one large merge — **except Phase 1**, which is destipak-only now (§6) and needs no paired
`django-trips` PR, unlike Phase 0 and the surface-B hardening in Phase 4A.

---

## 17. Task breakdown

Ordered by actual dependency, not by document order — §15 has the high-level diagram, this is
the checklist underneath it. Each task is tagged `[lib]` (`django_trips`) or `[destipak]`; 🔶
marks a task that's blocked on one of the §13 open decisions.

### Phase 0 tasks — ship first, nothing below depends on waiting for these, but do them anyway

No dependencies on each other or on anything downstream. Two of these are live bugs today, not
future-proofing — that's the actual reason to front-load them, not just habit.

- [x] **P0.1** [lib] Fix the booking IDOR (§4) — scope `TripBookingRetrieveUpdateViewSet
  .get_queryset()` to the requesting user. Own branch; ships independently of the entire rest of
  this document. Done on `fix/phase0-portability-and-idor`: `get_queryset()` now filters
  `TripBooking.objects.filter(created_by=self.request.user)`.
- [x] **P0.2** [lib] Fix §5.2 (**live bug**) — replace the concrete `django.contrib.auth.models
  .User` import in `api/serializers.py` (`UserSerializer.Meta.model`) and `tests/factories.py`
  (`UserFactory.Meta.model`) with `django.contrib.auth.get_user_model()`. Done — also found and
  fixed two more call sites the original audit missed: `api/tests/test_trip_delete.py` and
  `management/tests/test_generate_trips.py` both imported the same concrete `User` from
  `django_trips.models`, which broke at collection once P0.3 removed that name.
- [x] **P0.3** [lib] Fix §5.1 — replace `User = get_user_model()` at import time with the
  `settings.AUTH_USER_MODEL` string in FK `to=` params (`Trip.created_by` and any other lib FK
  built the same way). Bundle with P0.2 into one Phase 0 PR (§16). Done — also caught
  `TripBooking.created_by` and `TripWishlist.user`, two more FKs built the same way that weren't
  named explicitly in §5.1's text.
- [x] **P0.4** [lib] Add draft/publish state to `Trip` (§13.4) — a plain model field, unrelated
  to tenancy despite living conceptually near "Phase 1"; cheapest to bundle here since it's
  lib-side and needed well before Phase 6 (§11 point 4). Done — `TripStatus(models.TextChoices)`
  (`DRAFT`/`PUBLISHED`) added to `choices.py`, `Trip.status` field (`default=PUBLISHED`, so every
  existing row keeps its current, only-ever visibility), migration `0012_trip_status.py`.
  Deliberately scoped to **field + migration only** — nothing produces a `DRAFT` trip yet
  (operator signup is Phase 6/P6.1, unbuilt), so wiring it into `TripViewSet`'s public queryset
  now would be untested and would touch that view's already-fragile ordering/annotation logic for
  no present benefit. Filtering it into the public surface is Phase 4A's job (§9.1), once
  something can actually create a draft.
- [x] **P0.5** [lib] Write the booking IDOR regression test (§12) alongside P0.1, not later. Done
  — three regression tests added (retrieve/update/cancel), each asserting a non-owner gets 404
  against another user's booking.

**Verification for all of Phase 0 (P0.1–P0.5):** full suite 342 passed / 1 skipped, `manage.py
check` clean (one pre-existing unrelated `staticfiles.W004` warning), `makemigrations --check
--dry-run` reports no changes needed after each round, pylint 9.91/10. All on
`fix/phase0-portability-and-idor` (django-trips), branched off a freshly fast-forwarded `master`.
**Phase 0 is fully done. Not yet committed.**

### Phase 1 tasks — tenancy primitives (destipak, §6)

No hard dependency on Phase 0 (see §16's closing note) — can run in parallel with it. Everything
here is one app, so these are naturally one branch/PR, done roughly in this order because each
step imports the previous one.

🔶 **P1.0** Decide the app name (§13.2) before creating anything — every path below assumes it.

- [ ] **P1.1** [destipak] Create the app; add `HostRole` + `HostMembership` (§6.1) + migration.
- [ ] **P1.2** [destipak] `tenancy.py`: `get_manageable_hosts()`, `is_platform_staff()` (§6.2).
- [ ] **P1.3** [destipak] `tenancy.py`: `HOST_LOOKUP` + `for_host_member()` (§6.3),
  `for_customer()` (§6.4) — depends on P1.2 for `is_platform_staff`/`get_manageable_hosts`.
- [ ] **P1.4** [destipak] `permissions.py`: `IsHostMember`, `IsHostMemberOfObject` (§6.5) —
  depends on P1.2.

### Phase 2 tasks — auth foundation (destipak, §7)

Independent of Phase 1; can run in parallel with it.

- [ ] **P2.1** [lib] Remove `TokenObtainPairView`/`TokenRefreshView` from `django_trips/urls.py`.
- [ ] **P2.2** [destipak] Re-mount those endpoints in destipak's URLconf (`SIMPLE_JWT` config
  already lives there) — pairs with P2.1 in one PR per repo (§16).
- [ ] **P2.3** [destipak] 🔶 Build registration (signup, email verification, password reset) —
  blocked on **§13.1** (one signup flow vs. two); the endpoint/form shape depends on the answer.

### Phase 3 tasks — identity endpoint (destipak, §8)

Depends on **Phase 1** (P1.2, to populate `hosts: []`). Doesn't strictly need Phase 2 finished —
`login_view` already exists — but is far more testable once P2.3 gives you a second real user
to log in as.

- [ ] **P3.1** [destipak] `GET /api/me/`, using `get_manageable_hosts()` from P1.2.

### Phase 4 tasks — the three API surfaces (§9)

- [x] **P4.1** [lib] Harden surface B (§9.1) — narrow `TripViewSet.http_method_names`,
  drop `create`/`update`/`destroy` and the now-unused `IsStaffForDeleteOnly` import. No
  dependency on Phase 1/2/3 — done right after Phase 0. Landed as `["get", "post"]`, not bare
  `["get"]` — see §9.1's "gotcha" note (the `wishlist` extra action is POST and shares this
  class's `http_method_names`). Full details and known test-coverage gap in §9.1.
- [ ] **P4.2** [destipak] Surface A — operator viewsets/URLs (§9.2). **Hard dependency on Phase
  1** (P1.1–P1.4) — cannot start before those land.
- [ ] **P4.3** [destipak] Surface C — traveller profile viewsets (§9.3). Depends on **Phase 2**
  only (self-scoping via `created_by` never touches `HostMembership`) — can start before Phase 1
  is done.
  - 🔶 Subscription settings sub-task blocked on **§13.3** (`Subscriber` → `User` link).
  - Guest-booking claim-on-verified-email step needs P2.3's email verification first.

### Phase 5 tasks — frontend (§10)

Depends on **Phase 3** (route gating against `/api/me/`) and **Phase 4** (P4.2/P4.3 endpoints to
call).

- [ ] **P5.1** Resolve `src/booking-lookup-main.tsx`'s status (§10.1) first — precedent for
  multi-entry or dead code; changes how much of P5.2 is actually new work.
- [ ] **P5.2** Second Vite entry (`dashboard-main.tsx`) + move shared components out of the
  public route tree.
- [ ] **P5.3** Route structure + `beforeLoad` auth gating against `/api/me/` (§10.2) — depends
  on P3.1.
- [ ] **P5.4** Dashboard axios/TanStack Query wiring against the new `baseURL` (§10.3) — depends
  on P4.2 existing to call.
- [ ] **P5.5** Promote `/react-demo/` to real URLs (§10.4) — independent of P5.1–P5.4; sequence
  deliberately so it doesn't block the dashboard launch (§10.4).

### Phase 6 tasks — onboarding, verification, backfill (§11)

Depends on **Phase 1** (`HostMembership` must exist) and **Phase 2** (registration to attach the
transaction to). **Must** have P0.4 (draft/publish state) already decided and landed — retrofitting
after operators are live means a data migration over real rows.

- [ ] **P6.1** [destipak] Operator signup transaction: `User` + `Host` + `HostMembership(OWNER)`
  (§11) — depends on P1.1, P2.3.
- [ ] **P6.2** [destipak] Staff verification review flow in `stafftools`.
- [ ] **P6.3** [destipak] Confirm `HostManager.active()` excludes an unverified host's *trips*,
  not just the host itself (§11 point 3 flags this as unverified today — check it, don't assume).
- [ ] **P6.4** [destipak] `backfill_host_memberships` management command (§11 Data migration) —
  depends on P1.1.
  - 🔶 If backfill touches booking-state transitions, blocked on **§13.5** (which transitions an
    operator may perform) — confirm scope before writing it.

### Phase 7 tasks — verification (§12)

Write these incrementally as each phase above lands — don't batch them all to the end, that's
just a restatement of "test at the very end, right before shipping," which is the failure mode
this section exists to avoid.

- [ ] **P7.1** Booking IDOR regression test — with P0.1 (already listed as P0.5 above).
- [ ] **P7.2** `TenantIsolationTestMixin` — as soon as P4.2 exists.
- [ ] **P7.3** Public-surface anonymous/operator unscoped-read tests — as soon as P4.1 lands.
- [ ] **P7.4** Cross-surface booking matrix (four actors × three surfaces) — needs all of Phase 4
  (P4.1–P4.3).
- [ ] **P7.5** Client-supplied `host` rejection test — needs P4.2.
- [ ] **P7.6** Guest-booking claim-on-verified-email test — needs P4.3 + P2.3.
