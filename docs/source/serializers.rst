===========
Serializers
===========

By default, there are several serializers.


LookupQuerysetSerializer
------------------------

Serializer for retrieving options for a queryset:

Returning:

- ``id``: The pk value.
- ``name``: The value from a ``__str__`` method.


LookupChoiceSerializer
----------------------

Serializer for retrieving options for choices and booleans:

Returning:

- ``id``: The value of the choice.
- ``name``: The name of the choice.
