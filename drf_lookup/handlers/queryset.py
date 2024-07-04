from __future__ import annotations

import dataclasses
from contextlib import suppress
from typing import TYPE_CHECKING, NamedTuple

from django.core.exceptions import FieldError
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.settings import api_settings

from drf_lookup import settings
from drf_lookup.handlers.base import LookupBaseHandler
from drf_lookup.utils import get_field_queryset


if TYPE_CHECKING:
    from django.db.models import QuerySet


class FakeView(NamedTuple):
    """A named tuple representing a fake view.

    Attributes:
        search_fields (str): The fields to be used for searching.
        search_param (str): The parameter to be used for searching.
    """

    search_fields: str
    search_param: str


class NullElement(NamedTuple):
    """A named tuple representing a null element with a primary key and label.

    Attributes:
        pk (str): The primary key of the null element.
        label (str): The label of the null element.
    """

    pk: str
    label: str

    def __str__(self) -> str:
        """Return the string representation of the null element.

        Returns:
            str: The label of the null element.
        """
        return self.label


@dataclasses.dataclass
class LookupQuerySetHandler(LookupBaseHandler):
    """Handler for processing lookup querysets.

    This class provides functionality for handling lookup querysets in a DRF
    view, including filtering, pagination, and serialization.

    Attributes:
        field (Filter | Field): The field for which the lookup querysets are
            being handled.
        view (GenericViewSet): The view handling the request.
        request (Request): The request object.
        lookup (Lookup): The lookup configuration.
        parent_queryset (QuerySet | None): The parent queryset.
    """

    def filter_qs(self, qs) -> QuerySet:
        """Filter the queryset based on search fields and other criteria.

        Args:
            qs (QuerySet): The initial queryset to be filtered.

        Returns:
            QuerySet: The filtered queryset.
        """
        if search_fields := self.lookup.get(
            param='search_fields',
            default=getattr(qs.model, 'search_fields', None),
        ):
            qs = SearchFilter().filter_queryset(
                request=self.request,
                queryset=qs,
                view=FakeView(
                    search_fields=search_fields,
                    search_param=settings.DRF_LOOKUP_SEARCH_PARAM,
                ),
            )

        if self.parent_queryset:
            with suppress(FieldError):
                qs = qs.filter(
                    pk__in=self.parent_queryset.values(self.field_name)
                )

        if self.lookup.filterset:
            qs = self.lookup.filterset(
                queryset=qs,
                data=self.request.query_params,
            ).qs
        return qs

    def get_data(self, qs, serializer) -> list[dict]:
        """Serialize the queryset data and add a null element if needed.

        Args:
            qs (QuerySet): The queryset to serialize.
            serializer (Serializer): The serializer to use.

        Returns:
            list[dict]: The serialized data.
        """
        data = serializer(instance=qs, many=True).data

        if not self.null_label:
            return data

        with suppress(FieldError):
            if (
                self.parent_queryset
                and not self.parent_queryset.filter(
                    **{f'{self.field_name}__isnull': True}
                ).exists()
            ):
                return data

        null_element = NullElement(
            pk=self.field.field.null_value,
            label=self.null_label,
        )

        return [serializer(null_element).data, *data]

    @property
    def response(self) -> Response:
        """Generate the response for the lookup querysets.

        This method filters the querysets based on the specified criteria,
        applies pagination if required, and returns the serialized response.

        Returns:
            Response: The response containing the serialized querysets.
        """
        qs = self.filter_qs(get_field_queryset(self.field, self.request))

        serializer = self.lookup.get(
            param='serializer',
            default=settings.DRF_LOOKUP_QUERYSET_SERIALIZER,
        )

        if paginator_class := self.lookup.get(
            param='pagination_class',
            default=api_settings.DEFAULT_PAGINATION_CLASS,
        ):
            paginator = paginator_class()
            page = paginator.paginate_queryset(
                queryset=qs,
                request=self.request,
                view=self.view,
            )
            if page is not None:
                return paginator.get_paginated_response(
                    self.get_data(page, serializer)
                )

        return Response(self.get_data(qs, serializer))
