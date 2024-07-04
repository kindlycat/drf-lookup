from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django_filters import FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError
from rest_framework.fields import Field

from drf_lookup.lookup import Lookup


if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django_filters import Filter
    from rest_framework.generics import GenericAPIView
    from rest_framework.request import Request
    from rest_framework.serializers import Serializer


def get_lookup_action(view: GenericAPIView, request: Request) -> str:
    """Get the lookup action from the request.

    This function retrieves the 'lookup_action' from the request query
    parameters and validates it against the default and extra actions
    available in the view.

    Args:
        view (GenericAPIView): The DRF view.
        request (Request): The DRF request.

    Returns:
        str: The validated action name.

    Raises:
        ValidationError: If the action does not exist in the view.
    """
    action = request.query_params.get('lookup_action')

    default_actions = [
        name
        for name in ('list', 'create', 'update', 'partial_update', 'destroy')
        if hasattr(view, name)
    ]
    extra_actions = [x.__name__ for x in view.get_extra_actions()]

    if action not in default_actions + extra_actions:
        raise ValidationError('Action does not exist.')

    return action


def copy_attrs_from_view(
    lookup_view: GenericAPIView,
    action: str,
    attr_names: tuple[str],
) -> None:
    """Copy attributes from a view's action to the lookup view.

    This function copies specified attributes from an action view's kwargs to
    the lookup view if they exist.

    Args:
        lookup_view (GenericAPIView): The lookup view.
        action (str): The action name.
        attr_names (tuple[str]): The attribute names to copy.
    """
    action_view = getattr(lookup_view, action, None)
    action_view_kwargs = getattr(action_view, 'kwargs', None)

    if not (action_view and action_view_kwargs):
        return

    for attr_name in attr_names:
        attr_value = action_view_kwargs.get(
            attr_name,
            getattr(lookup_view, attr_name, None),
        )

        setattr(lookup_view, attr_name, attr_value)


def get_field_queryset(field: Field | Filter, request: Request) -> QuerySet:
    """Get the queryset for a field.

    This function returns the queryset associated with a field.

    Args:
        field (Field | Filter): The field object.
        request (Request): The DRF request.

    Returns:
        QuerySet: The queryset associated with the field.
    """
    if isinstance(field, Field):
        return field.get_queryset()
    return field.get_queryset(request)


def get_filterset_from_view(
    view: GenericAPIView,
    request: Request,
    **_,
) -> QuerySet:
    """Get the filterset from a view.

    This function retrieves the filterset for a view using DjangoFilterBackend.

    Args:
        view (GenericAPIView): The DRF view.
        request (Request): The DRF request.

    Returns:
        QuerySet: The queryset after applying the filterset.
    """
    return DjangoFilterBackend().get_filterset(
        request=request,
        queryset=view.get_queryset(),
        view=view,
    )


def get_serializer_from_view(
    view: GenericAPIView,
    instance: Any | None,
    **_,
) -> QuerySet:
    """Get the serializer from a view.

    This function retrieves the serializer for a view, optionally for a
    specific instance.

    Args:
        view (GenericAPIView): The DRF view.
        instance (Any | None): The instance to serialize.

    Returns:
        QuerySet: The serializer instance.
    """
    return view.get_serializer(instance=instance)


def get_field(
    view: GenericAPIView,
    request: Request,
    instance: Any | None,
    fields: list[str],
    target: FilterSet | Serializer,
) -> tuple[Field | Filter, Lookup, FilterSet | Serializer, QuerySet | None]:
    """Retrieve the field and its associated lookup from the given target.

    This function navigates through the target (FilterSet or Serializer) to
    locate the specified field and returns the field, its lookup configuration,
    the final target, and the parent queryset if applicable.

    Args:
        view (GenericAPIView): The DRF view handling the request.
        request (Request): The request object.
        instance (Any | None): The instance being processed, if any.
        fields (list[str]): A list of field names to navigate through.
        target (FilterSet | Serializer): The target object containing the
            fields.

    Returns:
        tuple[Field | Filter, Lookup, FilterSet | Serializer, QuerySet | None]:
            A tuple containing the located field, its lookup configuration,
            the final target, and the parent queryset if applicable.

    Raises:
        ValidationError: If the field does not exist in the target.
    """
    try:
        field_name = fields.pop(0)

        if isinstance(target, FilterSet):
            field = target.filters[field_name]
            parent_queryset = target.queryset
        else:
            field = None
            parent_queryset = None
            names = field_name.split('.')
            while names:
                field_name = names.pop(0)
                target = target if field is None else field
                field = target.fields[field_name]
    except (KeyError, IndexError) as e:
        raise ValidationError('Field does not exist.') from e

    # Unwrap child_relation or child fields if present
    field = getattr(field, 'child_relation', field)
    field = getattr(field, 'child', field)

    meta = getattr(target, 'Meta', None)
    field_lookup: Lookup = getattr(meta, 'lookups', {}).get(
        field_name, Lookup()
    )

    if fields and field_lookup.filterset:
        return get_field(
            view=view,
            request=request,
            instance=instance,
            fields=fields,
            target=field_lookup.filterset(
                data=request.query_params,
                queryset=get_field_queryset(field, request),
                request=request,
            ),
        )

    return field, field_lookup, target, parent_queryset
