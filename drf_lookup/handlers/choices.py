from __future__ import annotations

import dataclasses
from contextlib import suppress
from typing import TYPE_CHECKING

from django.core.exceptions import FieldError
from django_filters import Filter
from rest_framework.response import Response

from drf_lookup import settings
from drf_lookup.handlers.base import LookupBaseHandler


if TYPE_CHECKING:
    from collections.abc import Iterable


@dataclasses.dataclass
class LookupChoiceHandler(LookupBaseHandler):
    """Handler for processing lookup choices.

    This class provides functionality for handling lookup choices in a DRF
    view, including filtering and serialization.

    Attributes:
        field (Filter | Field): The field for which the lookup choices are
            being handled.
        view (GenericViewSet): The view handling the request.
        request (Request): The request object.
        lookup (Lookup): The lookup configuration.
        parent_queryset (QuerySet | None): The parent queryset.
    """

    def get_choices(self) -> Iterable:
        """Get the choices for the field.

        Returns:
            Iterable: The choices for the field.
        """
        if isinstance(self.field, Filter):
            return [x for x in self.field.field.choices if x[0]]
        return self.field.choices.items()

    @property
    def response(self) -> Response:
        """Generate the response for the lookup choices.

        This method filters the choices based on search parameters and
        other settings, and returns the serialized response.

        Returns:
            Response: The response containing the serialized choices.
        """
        choices = self.get_choices()

        if self.search_query:
            choices = [x for x in choices if self.search_query in x[1].lower()]

        serializer = self.lookup.get(
            param='serializer',
            default=settings.DRF_LOOKUP_CHOICE_SERIALIZER,
        )

        if self.parent_queryset:
            with suppress(FieldError):
                qs_values = (
                    self.parent_queryset.order_by()
                    .values_list(self.field_name, flat=True)
                    .distinct()
                )
                choices = [
                    x
                    for x in choices
                    if x[0] in qs_values
                    or (x[1] == self.null_label and None in qs_values)
                ]

        return Response(serializer(instance=choices, many=True).data)
