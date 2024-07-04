from unittest.mock import PropertyMock

import django_filters
import pytest
from django.test import override_settings
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.serializers import ModelSerializer

from drf_lookup.lookup import Lookup
from tests.app.filters import CategoryFilterSet
from tests.app.models import Article, ArticleType, Category, Tag
from tests.app.serializers import ArticleSerializer
from tests.app.views import ArticleViewSet


url = '/articles/lookup_serializer/'


class Paginator(PageNumberPagination):
    page_size = 1


@pytest.mark.django_db()
def test_serializer_lookup_fk(admin_client):
    Category.objects.create(name='Public')
    Category.objects.create(name='Nonpublic', is_public=False)

    params = {
        'lookup_action': 'create',
        'lookup_field': 'category',
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    assert response.json() == [{'id': 1, 'name': 'Public'}]


@pytest.mark.django_db()
def test_serializer_lookup_m2m(admin_client):
    Tag.objects.create(name='Public')
    Tag.objects.create(name='Nonpublic', is_public=False)

    params = {
        'lookup_action': 'create',
        'lookup_field': 'tags',
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    assert response.json() == [{'id': 1, 'name': 'Public'}]


@pytest.mark.django_db()
def test_serializer_lookup_choices(admin_client):
    params = {
        'lookup_action': 'create',
        'lookup_field': 'type_of',
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    assert response.json() == [
        {'id': 'news', 'name': 'News'},
        {'id': 'review', 'name': 'Review'},
    ]


@pytest.mark.django_db()
def test_serializer_bad_action_negative(admin_client):
    params = {
        'lookup_action': 'bad_action',
        'lookup_field': 'type_of',
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 400
    assert response.json() == ['Action does not exist.']


@pytest.mark.django_db()
def test_serializer_bad_field_negative(admin_client):
    params = {
        'lookup_action': 'create',
        'lookup_field': 'bad_field',
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 400
    assert response.json() == ['Field does not exist.']


@pytest.mark.django_db()
def test_serializer_check_permission_negative(client):
    params = {
        'lookup_action': 'create',
        'lookup_field': 'category',
    }

    response = client.get(path=url, data=params)

    assert response.status_code == 403


@pytest.mark.django_db()
def test_serializer_lookup_queryset_search(admin_client, mocker):
    mocker.patch.object(
        ArticleSerializer.Meta,
        attribute='lookups',
        new_callable=PropertyMock,
        return_value={'category': Lookup(search_fields=('name',))},
        create=True,
    )

    Category.objects.create(name='Category 1')
    Category.objects.create(name='Category 2')

    params = {
        'lookup_action': 'create',
        'lookup_field': 'category',
        'search': '1',
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    assert response.json() == [{'id': 1, 'name': 'Category 1'}]


@pytest.mark.django_db()
def test_serializer_lookup_choices_search(admin_client):
    params = {
        'lookup_action': 'create',
        'lookup_field': 'type_of',
        'search': ArticleType.NEWS.value,
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    assert response.json() == [{'id': 'news', 'name': 'News'}]


@pytest.mark.django_db()
def test_serializer_lookup_queryset_custom_serializer(admin_client, mocker):
    class CustomCategorySerializer(serializers.Serializer):
        id = serializers.ReadOnlyField()
        name = serializers.CharField()
        is_public = serializers.BooleanField()

    mocker.patch.object(
        ArticleSerializer.Meta,
        attribute='lookups',
        new_callable=PropertyMock,
        return_value={'category': Lookup(serializer=CustomCategorySerializer)},
        create=True,
    )

    Category.objects.create(name='Category 1')

    params = {
        'lookup_action': 'list',
        'lookup_field': 'category',
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    assert response.json() == [
        {
            'id': 1,
            'name': 'Category 1',
            'is_public': True,
        }
    ]


@pytest.mark.django_db()
def test_serializer_lookup_queryset_custom_filterset(admin_client, mocker):
    class CustomCategoryFilterSet(django_filters.FilterSet):
        id = django_filters.NumberFilter(lookup_expr='iexact')

    mocker.patch.object(
        ArticleSerializer.Meta,
        attribute='lookups',
        new_callable=PropertyMock,
        return_value={'category': Lookup(filterset=CustomCategoryFilterSet)},
        create=True,
    )

    Category.objects.create(name='Category 1')
    Category.objects.create(name='Category 11')

    params = {
        'lookup_action': 'list',
        'lookup_field': 'category',
        'id': 1,
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    assert response.json() == [{'id': 1, 'name': 'Category 1'}]


@pytest.mark.django_db()
def test_serializer_lookup_queryset_custom_filterset_similar_params(
    admin_client, mocker
):
    class CustomCategoryFilterSet(django_filters.FilterSet):
        id = django_filters.NumberFilter(lookup_expr='iexact')

    mocker.patch.object(
        ArticleSerializer.Meta,
        attribute='lookups',
        new_callable=PropertyMock,
        return_value={'category': Lookup(filterset=CustomCategoryFilterSet)},
        create=True,
    )

    Category.objects.create(name='Category 1')
    category = Category.objects.create(name='Category 2')
    article = Article.objects.create(
        title='Test',
        category=category,
    )

    params = {
        'lookup_action': 'update',
        'lookup_field': 'category',
        'lookup_object': article.pk,
        'id': 2,
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    assert response.json() == [{'id': 2, 'name': 'Category 2'}]


@pytest.mark.django_db()
def test_serializer_lookup_custom_action(admin_client):
    params = {
        'lookup_action': 'custom_create',
        'lookup_field': 'type_of',
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    assert response.json() == [{'id': 'ad', 'name': 'Ad'}]


@pytest.mark.django_db()
def test_serializer_lookup_update_action(admin_client):
    category = Category.objects.create(name='Category 1')
    Category.objects.create(name='Category 2')

    article = Article.objects.create(
        title='Test',
        category=category,
    )

    params = {
        'lookup_action': 'update',
        'lookup_field': 'category',
        'lookup_object': article.pk,
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    assert response.json() == [{'id': category.id, 'name': category.name}]


@pytest.mark.django_db()
def test_serializer_lookup_detail_negative(admin_client):
    params = {
        'lookup_action': 'update',
        'lookup_field': 'category',
        'lookup_object': 'bad_id',
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 400
    assert response.json() == ['Object not found.']


@pytest.mark.django_db()
def test_serializer_lookup_pagination(admin_client):
    Category.objects.create(name='Category 1')
    Category.objects.create(name='Category 2')

    params = {
        'lookup_action': 'create',
        'lookup_field': 'category',
    }

    with override_settings(
        REST_FRAMEWORK={
            'DEFAULT_PAGINATION_CLASS': (
                'tests.test_serializer_view.Paginator'
            )
        }
    ):
        response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    data = response.json()
    assert data['count'] == 2
    assert data['results'] == [
        {
            'id': 1,
            'name': 'Category 1',
        },
    ]


@pytest.mark.django_db()
def test_serializer_lookup_custom_pagination(admin_client, mocker):
    Category.objects.create(name='Category 1')
    Category.objects.create(name='Category 2')

    class Paginator(PageNumberPagination):
        page_size = 1

    mocker.patch.object(
        ArticleSerializer.Meta,
        attribute='lookups',
        new_callable=PropertyMock,
        return_value={
            'category': Lookup(pagination_class=Paginator),
        },
        create=True,
    )
    params = {
        'lookup_action': 'create',
        'lookup_field': 'category',
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    data = response.json()
    assert data['count'] == 2
    assert data['results'] == [
        {
            'id': 1,
            'name': 'Category 1',
        },
    ]


@pytest.mark.django_db()
def test_serializer_lookup_custom_pagination_unset(admin_client, mocker):
    Category.objects.create(name='Category 1')
    Category.objects.create(name='Category 2')

    mocker.patch.object(
        ArticleSerializer.Meta,
        attribute='lookups',
        new_callable=PropertyMock,
        return_value={
            'category': Lookup(pagination_class=None),
        },
        create=True,
    )
    params = {
        'lookup_action': 'create',
        'lookup_field': 'category',
    }

    with override_settings(
        REST_FRAMEWORK={
            'DEFAULT_PAGINATION_CLASS': (
                'tests.test_serializer_view.Paginator'
            )
        }
    ):
        response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    assert response.json() == [
        {
            'id': 1,
            'name': 'Category 1',
        },
        {
            'id': 2,
            'name': 'Category 2',
        },
    ]


@pytest.mark.django_db()
def test_serializer_lookup_unsupported_field(admin_client):
    params = {
        'lookup_action': 'list',
        'lookup_field': 'id',
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 400
    assert response.json() == ['Unsupported field.']


@pytest.mark.django_db()
def test_serializer_lookup_nested_filter_choices(mocker, admin_client):
    Category.objects.create(name='Category 1')

    mocker.patch.object(
        ArticleSerializer.Meta,
        attribute='lookups',
        new_callable=PropertyMock,
        return_value={
            'category': Lookup(filterset=CategoryFilterSet),
        },
        create=True,
    )

    params = {
        'lookup_action': 'create',
        'lookup_field': ['category', 'priority'],
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    assert response.json() == [
        {'id': 'low', 'name': 'Low'},
    ]


@pytest.mark.django_db()
def test_serializer_lookup_nested_filter_queryset(mocker, admin_client):
    Category.objects.create(name='Category 1', author=admin_client.user)

    mocker.patch.object(
        ArticleSerializer.Meta,
        attribute='lookups',
        new_callable=PropertyMock,
        return_value={
            'category': Lookup(filterset=CategoryFilterSet),
        },
        create=True,
    )

    params = {
        'lookup_action': 'create',
        'lookup_field': ['category', 'author'],
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    assert response.json() == [
        {'id': admin_client.user.pk, 'name': str(admin_client.user)},
    ]


@pytest.mark.django_db()
def test_serializer_lookup_nested_serializer_choices(mocker, admin_client):
    class TestCategorySerializer(ModelSerializer):
        class Meta:
            model = Category
            fields = ['priority']

    class TestArticleSerializer(ModelSerializer):
        category = TestCategorySerializer()

        class Meta:
            model = Article
            fields = ['category']

    mocker.patch.object(
        ArticleViewSet,
        attribute='serializer_class',
        new_callable=PropertyMock,
        return_value=TestArticleSerializer,
    )

    params = {
        'lookup_action': 'create',
        'lookup_field': ['category.priority'],
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    assert response.json() == [
        {'id': 'low', 'name': 'Low'},
        {'id': 'medium', 'name': 'Medium'},
        {'id': 'high', 'name': 'High'},
    ]


@pytest.mark.django_db()
def test_serializer_lookup_nested_serializer_queryset(mocker, admin_client):
    class TestCategorySerializer(ModelSerializer):
        class Meta:
            model = Category
            fields = ['author']

    class TestArticleSerializer(ModelSerializer):
        category = TestCategorySerializer()

        class Meta:
            model = Article
            fields = ['category']

    mocker.patch.object(
        ArticleViewSet,
        attribute='serializer_class',
        new_callable=PropertyMock,
        return_value=TestArticleSerializer,
    )

    params = {
        'lookup_action': 'create',
        'lookup_field': ['category.author'],
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    assert response.json() == [
        {'id': admin_client.user.pk, 'name': str(admin_client.user)},
    ]
