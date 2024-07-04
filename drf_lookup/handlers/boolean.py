from __future__ import annotations

import dataclasses
from contextlib import suppress
from functools import cached_property
from typing import ClassVar

from django.core.exceptions import FieldError
from django.utils.translation import gettext_lazy as _
from django_filters import Filter
from rest_framework.response import Response

from drf_lookup import settings
from drf_lookup.handlers.base import LookupBaseHandler


@dataclasses.dataclass
class LookupBooleanHandler(LookupBaseHandler):
    """Handler for processing boolean field lookups.

    This class provides functionality for handling boolean field lookups in
    a DRF view, including filtering and serialization of choices.

    Attributes:
        field (Filter | Field): The field for which the lookup choices are
            being handled.
        view (GenericViewSet): The view handling the request.
        request (Request): The request object.
        lookup (Lookup): The lookup configuration.
        parent_queryset (QuerySet | None): The parent queryset.
    """

    map_db_values: ClassVar = {
        True: 'true',
        False: 'false',
        None: 'null',
    }

    @cached_property
    def choices(self) -> dict:
        """Get the choices for the boolean field.

        This method returns a dictionary mapping the possible boolean values
        to their display labels.

        Returns:
            dict: A dictionary with the boolean choices.
        """
        choices = {
            'true': _('Yes'),
            'false': _('No'),
        }

        if isinstance(self.field, Filter) or self.field.allow_null:
            choices = {'null': _('Unknown')} | choices

        return choices

    @property
    def response(self) -> Response:
        """Generate the response for the boolean field lookup.

        This method filters the choices based on the specified criteria and
        returns the serialized response.

        Returns:
            Response: The response containing the serialized choices.
        """
        choices = tuple(self.choices.items())

        if self.search_query:
            choices = [x for x in choices if self.search_query in x[1].lower()]

        if self.parent_queryset:
            with suppress(FieldError):
                qs_values = (
                    self.parent_queryset.order_by()
                    .values_list(
                        self.field_name,
                        flat=True,
                    )
                    .distinct()
                )
                qs_values = [self.map_db_values[x] for x in qs_values]

                choices = [x for x in choices if x[0] in qs_values]

        serializer = self.lookup.get(
            param='serializer',
            default=settings.DRF_LOOKUP_CHOICE_SERIALIZER,
        )

        return Response(serializer(instance=choices, many=True).data)
