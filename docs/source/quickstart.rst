==========
Quickstart
==========


Installation
============

Install it from PyPI:

.. code-block:: bash

    $ pip install drf-lookup


Usage
=====

For example, you have some models:

.. code-block:: python

    from django.db import models

    class Category(models.Model):
        name = models.CharField(max_length=100, db_index=True)
        is_public = models.BooleanField(default=True)

        class Meta:
            verbose_name = 'category'
            verbose_name_plural = 'categories'
            ordering = ['name', 'pk']

        def __str__(self) -> str:
            return self.name


    class Article(models.Model):
        title = models.CharField(max_length=100, db_index=True)
        category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)

        class Meta:
            verbose_name = 'news'
            verbose_name_plural = 'news'
            ordering = ['-pk']

        def __str__(self) -> str:
            return self.title


Serializer for Article:

.. code-block:: python

    from rest_framework.serializers import ModelSerializer

    class ArticleSerializer(ModelSerializer):
        class Meta:
            model = Article
            fields = ('id', 'title', 'category')
            extra_kwargs = {
                'category': {
                    'queryset': Category.objects.filter(is_public=True),
                },
            }


And filterset for Article:

.. code-block:: python

    import django_filters

    class ArticleFilterSet(django_filters.FilterSet):
        class Meta:
            model = Article
            fields = ('category',)


Add Lookup mixin to the view:

.. code-block:: python

    from rest_framework.viewsets import ModelViewSet

    from drf_lookup.views import LookupMixin


    class ArticleViewSet(LookupMixin, ModelViewSet):
        queryset = Article.objects.all()
        serializer_class = ArticleSerializer
        filterset_class = ArticleFilterSet


This mixin will add additional actions: ``lookup_serializer`` and
``lookup_filter``.

Now, we can request options for the `category` field.

.. code-block:: json

    // GET /api/articles/lookup_serializer/?lookup_action=create&lookup_field=category
    // Only public categories will be returned

    [
      {
        "id": 1,
        "name": "Public category"
      },
      {
        "id": 2,
        "name": "Public category 2"
      }
    ]

.. code-block:: json

    // GET /api/articles/lookup_filter/?lookup_action=list&lookup_field=category
    // Only categories specified in articles will be returned

    [
      {
        "id": 1,
        "name": "Public category"
      },
    ]
