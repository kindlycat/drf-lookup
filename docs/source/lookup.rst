======
Lookup
======

There is the ``Lookup`` dataclass for defining lookup configurations.
To customize lookups you should define ``lookups`` dictionary in the
serializer's Meta class.

Valid parameters:

- ``serializer``: A custom serializer for options.
- ``filterset``: If you need a custom filter, for example, if you have a modal
  on the frontend with an object list and filters, you can define a custom
  filterset.
- ``search_fields``: Every lookup has a search filter by default. If it is a
  queryset field, you can define the model's fields to be used for search,
  or alternatively, you can define it as a property in the model.
- ``pagination_class``: A pagination class, or ``None`` if you don't need it.


Example:

.. code-block:: python

    from drf_lookup import Lookup
    from rest_framework import serializers


    class LookupCategorySerializer(serializers.Serializer):
        id = serializers.ReadOnlyField(source='pk')
        name = serializers.ReadOnlyField(source='__str__')
        is_public = serializers.BooleanField()


    class ArticleSerializer(serializers.ModelSerializer):
        class Meta:
            model = Article
            fields = ('id', 'title', 'category')
            lookups = {
                'category': Lookup(serializer=LookupCategorySerializer),
            }
