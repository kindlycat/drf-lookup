# Drf-lookup

Drf-lookup helps you retrieve options for serializer fields and django-filter
filters. It adds additional actions to the viewset, checks the ``queryset`` and
``choices`` attributes and returns valid values for the requested field/filter. 
This is useful when you are retrieving parameters asynchronously and don't need 
to create a view for each case.

## Install

```bash
pip install drf-lookup
```

## Example

```python

# models
from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    is_public = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        ordering = ['name']

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


# Create some objects
category = Category.objects.create(name='Category 1')
Category.objects.create(name='Category 2', is_public=False)
Category.objects.create(name='Category 3')
Article.objects.create(title='Test title', category=category)


# serializers
from rest_framework.serializers import ModelSerializer

class ArticleSerializer(ModelSerializer):
    class Meta:
        model = Article
        fields = ('id', 'title', 'category')

        # Limit categories by the `is_public` attribute
        extra_kwargs = {
            'category': {'queryset': Category.objects.filter(is_public=True)},
        }

# filters
import django_filters

class ArticleFilterSet(django_filters.FilterSet):
    class Meta:
        model = Article
        fields = ('category',)


# views
from rest_framework.viewsets import ModelViewSet

from drf_lookup.views import LookupMixin


class ArticleViewSet(LookupMixin, ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    filterset_class = ArticleFilterSet
```

Now, it's possible to retrieve valid options for the serializer's `category` field.

```json
// GET /api/articles/lookup_serializer/?lookup_action=create&lookup_field=category
// Only public categories will be returned

[
  {
    "id": 1,
    "name": "Category 1"
  },
  {
    "id": 3,
    "name": "Category 3"
  }
]
```

And for the filter's `category` field.
```json
// GET /api/articles/lookup_filter/?lookup_action=list&lookup_field=category
// Only categories specified in articles will be returned

[
  {
    "id": 1,
    "name": "Category 1"
  },
]
```

