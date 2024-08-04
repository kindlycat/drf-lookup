========
Settings
========

``DRF_LOOKUP_CHOICE_SERIALIZER``
--------------------------------

Default: ``'drf_lookup.serializers.LookupChoiceSerializer'``

Path to the serializer that retrieves choice and boolean options.


``DRF_LOOKUP_QUERYSET_SERIALIZER``
----------------------------------

Default: ``'drf_lookup.serializers.LookupQuerysetSerializer'``

Path to the serializer that retrieves queryset options.


``DRF_LOOKUP_SEARCH_PARAM``
---------------------------

Default: ``'from rest_framework.settings.api_settings.SEARCH_PARAM'``

The name of a query parameter, which can be used to specify the search term.
