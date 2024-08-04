======
Mixins
======

This package has several mixins which add lookup functionality.

- ``LookupMixin``: Add lookup actions for serializers and filters.
- ``LookupSerializerMixin``: Add lookup action for serializers.
- ``LookupFilterMixin``: Add lookup action for filters.

lookup_serializer
-----------------
The action that adds lookup functionality for serializers to the view.

Parameters:

- ``lookup_action``: The view's action (create/update/custom).
- ``lookup_field``: The field for which options are requested.
- ``lookup_object``: The model instance's primary key, for example, for update action.

lookup_filter
-------------
The action that adds lookup functionality for filters to the view.

Parameters:

- ``lookup_action``: The view's action (create/update/custom).
- ``lookup_field``: The field for which options are requested.
