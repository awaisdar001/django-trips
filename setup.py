import os
import re

from setuptools import setup, setup, find_packages

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()


def get_version(*file_paths):
    """
    Extract the version string from the file at the given relative path fragments.
    """
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = open(filename).read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


def package_data(pkg, root_list):
    """
    Generic function to find package_data for `pkg` under `root`.
    """
    data = []
    for root in root_list:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}


def is_requirement(line):
    """
    Return True if the requirement line is a package requirement.

    Returns:
        bool: True if the line is not blank, a comment, a URL, or an included file
    """
    return not (
            line == '' or
            line.startswith('-r') or
            line.startswith('#') or
            line.startswith('-e') or
            line.startswith('git+')
    )


def load_requirements(*requirements_paths):
    """
    Load all requirements from the specified requirements files.

    Returns:
        list: Requirements file relative path strings
    """
    requirements = set()
    for path in requirements_paths:
        requirements.update(
            line.split('#')[0].strip() for line in open(path).readlines()
            if is_requirement(line.strip())
        )
    return list(requirements)


VERSION = get_version('django_trips', '__init__.py')

setup(
    name='django - trips',
    version=VERSION,
    description='A Django Rest API for fetching and creating trips and their schedules.',
    long_description=README,
    long_description_content_type='text/markdown',
    url='https://github.com/awaisdar001/django-trips',
    author='Awais Jibran',
    author_email='awaisdar001@gmail.com',
    license='MIT License',
    keywords='Django trips',
    packages=['django_trips'],
    install_requires=['setuptools'],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    include_package_data=True,
    package_data=package_data("django_trips", ["static"]),
    entery_points={
        'django_trips': [
            'django_trips = django_trips'
        ]
    },

)
