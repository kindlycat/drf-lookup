from django.conf import settings
from django.utils.module_loading import import_string
from rest_framework.settings import api_settings


# Default serializer for choices
DRF_LOOKUP_CHOICE_SERIALIZER = import_string(
    getattr(
        settings,
        'DRF_LOOKUP_CHOICE_SERIALIZER',
        'drf_lookup.serializers.LookupChoiceSerializer',
    )
)


# Default serializer for queryset
DRF_LOOKUP_QUERYSET_SERIALIZER = import_string(
    getattr(
        settings,
        'DRF_LOOKUP_QUERYSET_SERIALIZER',
        'drf_lookup.serializers.LookupQuerysetSerializer',
    )
)


# Search param for lookup
DRF_LOOKUP_SEARCH_PARAM = api_settings.SEARCH_PARAM
