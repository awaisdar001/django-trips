"""Setup file for django-trips"""
import setuptools


def load_requirements(*requirements_paths):
    """
    Load all requirements from the specified requirements files.
    Returns a list of requirement strings.
    """
    requirements = set()
    for path in requirements_paths:
        requirements.update(
            line.strip() for line in open(path).readlines()
            if is_requirement(line)
        )
    return list(requirements)


def is_requirement(line):
    """
    Return True if the requirement line is a package requirement;
    that is, it is not blank, a comment, or editable.
    """
    # Remove whitespace at the start/end of the line
    line = line.strip()

    # Skip blank lines, comments, and editable installs
    return not (
            line == '' or
            line.startswith('-r') or
            line.startswith('#') or
            line.startswith('-e') or
            line.startswith('git+') or
            line.startswith('-c')
    )


with open("README.md") as fh:
    long_description = fh.read()

setuptools.setup(
    name="django-trips",
    version="0.2.1",
    author="Awais Jibran",
    author_email="awaisdar001@gmail.com",
    description="An Django Rest API for fetching and creating trips and their schedules.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/awaisdar001/django-trips",
    license='AGPL',
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
    install_requires=load_requirements('django_trips/requirements.txt'),
)
