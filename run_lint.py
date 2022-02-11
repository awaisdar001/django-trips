import sys

import pylint.lint
THRESHOLD = 6

pylint_opts = [
    '--disable=line-too-long --load-plugins pylint_django --django-settings-module=settings.test',
    './django_trips'
]
results = pylint.lint.Run(pylint_opts, do_exit=False)
score = round(results.linter.stats.global_note, 2)

if score < THRESHOLD:
    sys.stdout.write(f'Code quality is below the threshold {score}/{THRESHOLD}.\n')
    sys.exit(1)
