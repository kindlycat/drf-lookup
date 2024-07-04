from __future__ import annotations

import abc
import dataclasses
from typing import TYPE_CHECKING

from django_filters import Filter

from drf_lookup import settings


if TYPE_CHECKING:
    from django.db.models import QuerySet
    from rest_framework.fields import Field
    from rest_framework.request import Request
    from rest_framework.response import Response
    from rest_framework.viewsets import GenericViewSet

    from drf_lookup.lookup import Lookup


@dataclasses.dataclass
class LookupBaseHandler(abc.ABC):
    """Abstract base class for handling lookups in DRF views.

    This class provides a structure for handling lookups on fields within
    a Django Rest Framework view.

    Attributes:
        field (Filter | Field): The field or filter to be looked up.
        view (GenericViewSet): The DRF view.
        request (Request): The request object.
        lookup (Lookup): The lookup condition to be applied.
        parent_queryset (QuerySet | None): The parent queryset, if any.
    """

    field: Filter | Field
    view: GenericViewSet
    request: Request
    lookup: Lookup
    parent_queryset: QuerySet | None

    @property
    @abc.abstractmethod
    def response(self) -> Response:
        return NotImplementedError

    @property
    def field_name(self):
        if field_name := getattr(self.field, 'field_name', None):
            return field_name
        return self.field.source.replace('.', '__')

    @property
    def null_label(self):
        if not isinstance(self.field, Filter):
            return None

        return self.field.field.null_label

    @property
    def search_query(self) -> str | None:
        if search_query := self.request.query_params.get(
            settings.DRF_LOOKUP_SEARCH_PARAM
        ):
            return search_query.lower()
