from settings.common import *
from path import Path as path

TEST_ROOT = path('test_root')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': TEST_ROOT / "db" / "trips.db",
        'ATOMIC_REQUESTS': True,
    },
}
