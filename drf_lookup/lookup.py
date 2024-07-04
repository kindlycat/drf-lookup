from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Iterable

    from django_filters import FilterSet
    from rest_framework.pagination import BasePagination
    from rest_framework.serializers import Serializer


class Unset:
    """A sentinel class to represent unset or undefined values."""


@dataclasses.dataclass
class Lookup:
    """Class for defining lookup configurations.

    Attributes:
        serializer (type[Serializer] | None): The serializer class for the
            lookup.
        filterset (type[FilterSet] | None): The filterset class for the
            lookup.
        search_fields (Iterable[str] | Unset | None): The search fields for
            the lookup.
        pagination_class (type[BasePagination] | Unset | None): The pagination
            class for the lookup.
    """

    serializer: type[Serializer] | Unset = Unset
    filterset: type[FilterSet] | None = None
    search_fields: Iterable[str] | Unset | None = Unset
    pagination_class: type[BasePagination] | Unset | None = Unset

    def get(self, param: str, default=None) -> Any:
        """Get the value of the specified parameter.

        This method returns the value of the specified parameter if it is
        not Unset. Otherwise, it returns the default value.

        Args:
            param (str): The name of the parameter to retrieve.
            default (Any): The default value to return if the parameter is
                Unset.

        Returns:
            Any: The value of the specified parameter or the default value.
        """
        value = getattr(self, param)
        if value is not Unset:
            return value
        return default
