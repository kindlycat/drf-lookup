from __future__ import annotations

from typing import TYPE_CHECKING

from django.http import Http404
from django_filters import (
    BooleanFilter,
    ChoiceFilter,
    Filter,
    ModelChoiceFilter,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
)
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, ChoiceField, Field
from rest_framework.relations import RelatedField

from drf_lookup.handlers.boolean import LookupBooleanHandler
from drf_lookup.handlers.choices import LookupChoiceHandler
from drf_lookup.handlers.queryset import LookupQuerySetHandler
from drf_lookup.utils import (
    copy_attrs_from_view,
    get_field,
    get_filterset_from_view,
    get_lookup_action,
    get_serializer_from_view,
)


if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from rest_framework.request import Request
    from rest_framework.response import Response

    from drf_lookup.handlers.base import LookupBaseHandler


class LookupBase:
    """Base view class for handling lookups."""

    def lookup_get_field_handler_class(
        self,
        field: Field | Filter,
    ) -> type[LookupBaseHandler]:
        """Determine the appropriate handler class for a given field.

        This method checks the type of the field and returns the corresponding
        handler class.

        Args:
            field (Field | Filter): The field for which the handler class is
                to be determined.

        Returns:
            type[LookupBaseHandler]: The handler class corresponding to the
                field type.

        Raises:
            ValidationError: If the field type is unsupported.
        """
        if isinstance(
            field, ModelChoiceFilter | ModelMultipleChoiceFilter | RelatedField
        ):
            return LookupQuerySetHandler

        if isinstance(
            field, ChoiceFilter | MultipleChoiceFilter | ChoiceField
        ):
            return LookupChoiceHandler

        if isinstance(field, BooleanFilter | BooleanField):
            return LookupBooleanHandler

        raise ValidationError('Unsupported field.')

    def lookup_get_instance(self, request: Request) -> Any:
        """Retrieve the instance for the lookup.

        Args:
            request (Request): The request object.

        Returns:
            Any: The retrieved instance.

        Raises:
            ValidationError: If the object is not found.
        """
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        self.kwargs[lookup_url_kwarg] = request.query_params.get(
            'lookup_object'
        )

        if not self.kwargs.get(lookup_url_kwarg):
            return None

        # Unset filterset_class to prevent filtering in get_object
        original_filterset_class = getattr(self, 'filterset_class', None)
        self.filterset_class = None

        try:
            return self.get_object()
        except Http404 as e:
            raise ValidationError('Object not found.') from e
        finally:
            self.filterset_class = original_filterset_class

    def lookup_response(
        self,
        request: Request,
        target_getter: Callable,
        attrs_to_copy: tuple[str, ...],
    ) -> Response:
        """Generate the response for the lookup.

        Args:
            request (Request): The request object.
            target_getter (Callable): The function to get the target.
            attrs_to_copy (tuple[str, ...]): Attributes to copy from the view.

        Returns:
            Response: The generated response.
        """
        # Act like action from lookup_action
        self.action = get_lookup_action(view=self, request=request)

        self.check_permissions(request)

        copy_attrs_from_view(
            lookup_view=self,
            action=self.action,
            attr_names=attrs_to_copy,
        )

        instance = self.lookup_get_instance(request=request)

        field, field_lookup, _, parent_queryset = get_field(
            view=self,
            request=request,
            instance=instance,
            fields=request.query_params.getlist('lookup_field'),
            target=target_getter(
                view=self,
                request=request,
                instance=instance,
            ),
        )

        handler_class = self.lookup_get_field_handler_class(field)

        handler = handler_class(
            field=field,
            view=self,
            request=request,
            lookup=field_lookup,
            parent_queryset=parent_queryset,
        )

        return handler.response


class LookupSerializerMixin(LookupBase):
    """Mixin class for serializer-based lookups."""

    @action(detail=False, methods=['get'])
    def lookup_serializer(self, request, **kwargs) -> Response:
        """Handle the lookup for serializers.

        Args:
            request (Request): The request object.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: The response for the serializer lookup.
        """
        return self.lookup_response(
            request=request,
            target_getter=get_serializer_from_view,
            attrs_to_copy=('serializer_class', 'queryset'),
        )


class LookupFilterMixin(LookupBase):
    """Mixin class for filter-based lookups."""

    @action(detail=False, methods=['get'])
    def lookup_filter(self, request, **kwargs) -> Response:
        """Handle the lookup for filters.

        Args:
            request (Request): The request object.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: The response for the filter lookup.
        """
        return self.lookup_response(
            request=request,
            target_getter=get_filterset_from_view,
            attrs_to_copy=('filterset_class', 'filterset_fields', 'queryset'),
        )


class LookupMixin(LookupSerializerMixin, LookupFilterMixin):
    """Mixin class that combines serializer and filter-based lookups."""
