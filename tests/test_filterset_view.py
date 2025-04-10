from unittest.mock import PropertyMock

import django_filters
import pytest
from rest_framework import serializers

from drf_lookup import Lookup
from tests.app.filters import ArticleFilterSet, CategoryFilterSet
from tests.app.models import ArticleType, Category, Tag


url = '/articles/lookup_filter/'


@pytest.mark.django_db
def test_filter_lookup_fk(admin_client):
    Category.objects.create(name='Public')
    Category.objects.create(name='Nonpublic', is_public=False)

    params = {
        'lookup_action': 'list',
        'lookup_field': 'category',
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    assert response.json() == [{'id': 1, 'name': 'Public'}]


@pytest.mark.django_db
def test_filter_lookup_m2m(admin_client):
    Tag.objects.create(name='Public')
    Tag.objects.create(name='Nonpublic', is_public=False)

    params = {
        'lookup_action': 'list',
        'lookup_field': 'tags',
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    assert response.json() == [{'id': 1, 'name': 'Public'}]


@pytest.mark.django_db
def test_filter_lookup_choices(admin_client):
    params = {
        'lookup_action': 'list',
        'lookup_field': 'type_of',
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    assert response.json() == [
        {'id': 'news', 'name': 'News'},
        {'id': 'review', 'name': 'Review'},
    ]


@pytest.mark.django_db
def test_filter_lookup_boolean(admin_client):
    params = {
        'lookup_action': 'list',
        'lookup_field': 'is_published',
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    assert response.json() == [
        {'id': 'null', 'name': 'Unknown'},
        {'id': 'true', 'name': 'Yes'},
        {'id': 'false', 'name': 'No'},
    ]


@pytest.mark.django_db
def test_filter_bad_action_negative(admin_client):
    params = {
        'lookup_action': 'bad_action',
        'lookup_field': 'tags',
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 400
    assert response.json() == ['Action does not exist.']


@pytest.mark.django_db
def test_filter_bad_field_negative(admin_client):
    params = {
        'lookup_action': 'list',
        'lookup_field': 'bad_field',
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 400
    assert response.json() == ['Field does not exist.']


@pytest.mark.django_db
def test_filter_check_permission_negative(client):
    params = {
        'lookup_action': 'list',
        'lookup_field': 'category',
    }

    response = client.get(path=url, data=params)

    assert response.status_code == 403


@pytest.mark.django_db
def test_filter_lookup_queryset_search(admin_client, mocker):
    mocker.patch.object(
        ArticleFilterSet.Meta,
        attribute='lookups',
        new_callable=PropertyMock,
        return_value={'category': Lookup(search_fields=('name',))},
        create=True,
    )

    Category.objects.create(name='Category 1')
    Category.objects.create(name='Category 2')

    params = {
        'lookup_action': 'list',
        'lookup_field': 'category',
        'search': '1',
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    assert response.json() == [{'id': 1, 'name': 'Category 1'}]


@pytest.mark.django_db
def test_filter_lookup_choices_search(admin_client):
    params = {
        'lookup_action': 'list',
        'lookup_field': 'type_of',
        'search': ArticleType.NEWS.value,
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    assert response.json() == [{'id': 'news', 'name': 'News'}]


@pytest.mark.django_db
def test_filter_lookup_boolean_search(admin_client):
    params = {
        'lookup_action': 'list',
        'lookup_field': 'is_published',
        'search': 'Y',
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    assert response.json() == [{'id': 'true', 'name': 'Yes'}]


@pytest.mark.django_db
def test_filter_lookup_queryset_custom_serializer(admin_client, mocker):
    class CustomCategorySerializer(serializers.Serializer):
        id = serializers.ReadOnlyField()
        name = serializers.CharField()
        is_public = serializers.BooleanField()

    mocker.patch.object(
        ArticleFilterSet.Meta,
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


@pytest.mark.django_db
def test_filter_lookup_queryset_custom_filterset(admin_client, mocker):
    class CustomCategoryFilterSet(django_filters.FilterSet):
        id = django_filters.NumberFilter()

    mocker.patch.object(
        ArticleFilterSet.Meta,
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


@pytest.mark.django_db
def test_filter_lookup_custom_action(admin_client):
    params = {
        'lookup_action': 'custom_list',
        'lookup_field': 'type_of',
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 200
    assert response.json() == [{'id': 'ad', 'name': 'Ad'}]


@pytest.mark.django_db
def test_filter_lookup_unsupported_field(admin_client):
    params = {
        'lookup_action': 'list',
        'lookup_field': 'id',
    }

    response = admin_client.get(path=url, data=params)

    assert response.status_code == 400
    assert response.json() == ['Unsupported field.']


@pytest.mark.django_db
def test_filter_lookup_nested_filter_choices(mocker, admin_client):
    Category.objects.create(name='Category 1')

    mocker.patch.object(
        ArticleFilterSet.Meta,
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


@pytest.mark.django_db
def test_filter_lookup_nested_filter_queryset(mocker, admin_client):
    Category.objects.create(name='Category 1', author=admin_client.user)

    mocker.patch.object(
        ArticleFilterSet.Meta,
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
