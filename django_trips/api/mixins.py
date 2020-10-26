"""API Mixins"""
from rest_framework.generics import get_object_or_404


class MultipleFieldLookupMixin(object):
    """Mixin for using multi field lookups."""

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())  # Apply any filter backends
        filter = {}
        for field in self.lookup_fields:
            if self.kwargs.get(field):
                filter[field] = self.kwargs[field]

        obj = get_object_or_404(queryset, **filter)  # Lookup the object
        self.check_object_permissions(self.request, obj)
        return obj
