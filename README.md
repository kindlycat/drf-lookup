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


# serializers
from rest_framework.serializers import ModelSerializer
class ArticleSerializer(ModelSerializer):
    class Meta:
        model = Article
        fields = ('id', 'title', 'category')


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

Now, we can request options for the `category` field:

```
GET /articles/lookup_serializer/?lookup_action=create&lookup_field=category

GET /articles/lookup_filterset/?lookup_action=list&lookup_field=category
```
