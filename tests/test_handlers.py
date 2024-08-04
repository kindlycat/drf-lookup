from __future__ import annotations

from typing import TYPE_CHECKING

import django_filters
import pytest
from django.test import RequestFactory
from rest_framework import serializers
from rest_framework.request import Request

from drf_lookup import Lookup
from drf_lookup.handlers.boolean import LookupBooleanHandler
from drf_lookup.handlers.choices import LookupChoiceHandler
from drf_lookup.handlers.queryset import LookupQuerySetHandler
from tests.app.models import Article, ArticleType, Category, CategoryPriority


if TYPE_CHECKING:
    from django.db.models import QuerySet

    from drf_lookup.handlers.base import LookupBaseHandler


class ChoiceCustomSerializer(serializers.Serializer):
    def to_representation(self, instance):
        return instance[1]


class ObjectCustomSerializer(serializers.Serializer):
    def to_representation(self, instance):
        return str(instance)


@pytest.mark.django_db()
class HandlerTests:
    field_class: type[django_filters.Filter | serializers.Serializer]
    handler_class: type[LookupBaseHandler]
    expected: list[dict]
    field_kwargs: dict
    field_custom_serializer: type[serializers.Serializer]
    custom_serializer_expected: list[str]
    parent_queryset: QuerySet[Article] | None

    def run_test_handler_with_search(
        self, view, search, expected, lookup=None
    ):
        handler = self.handler_class(
            field=self.field_class(**self.field_kwargs),
            view=view,
            request=Request(RequestFactory().get('/', {'search': search})),
            lookup=lookup or Lookup(),
            parent_queryset=self.parent_queryset,
        )

        assert handler.response.data == expected

    def test_handler_with_search(self, *args, **kwargs):
        raise NotImplementedError

    def test_handler_positive(self, view):
        Article.objects.create(
            title='First article',
            type_of=ArticleType.NEWS,
            is_published=True,
        )
        handler = self.handler_class(
            field=self.field_class(**self.field_kwargs),
            view=view,
            request=Request(RequestFactory().get('/')),
            lookup=Lookup(),
            parent_queryset=self.parent_queryset,
        )

        assert handler.response.data == self.expected

    def test_handler_custom_serializer(self, view):
        Article.objects.create(title='First article', type_of=ArticleType.NEWS)
        handler = self.handler_class(
            field=self.field_class(**self.field_kwargs),
            view=view,
            request=Request(RequestFactory().get('/')),
            lookup=Lookup(serializer=self.field_custom_serializer),
            parent_queryset=self.parent_queryset,
        )

        assert handler.response.data == self.custom_serializer_expected


class TestChoiceFilter(HandlerTests):
    field_class = django_filters.ChoiceFilter
    handler_class = LookupChoiceHandler
    expected = [
        {'id': 'news', 'name': 'News'},
    ]
    custom_serializer_expected = [ArticleType.NEWS.label]
    with_null_expected = [
        {'id': 'null', 'name': 'No value'},
        {'id': 'news', 'name': 'News'},
    ]
    field_custom_serializer = ChoiceCustomSerializer

    @property
    def parent_queryset(self) -> QuerySet[Article]:
        return Article.objects.all()

    @property
    def field_kwargs(self):
        return {
            'choices': ArticleType.choices,
            'null_label': 'No value',
            'field_name': 'type_of',
        }

    def test_handler_with_null_positive(self, view):
        Article.objects.create(title='Test', type_of=ArticleType.NEWS)
        Article.objects.create(title='Test', type_of=None, is_published=None)

        handler = self.handler_class(
            field=self.field_class(**self.field_kwargs),
            view=view,
            request=Request(RequestFactory().get('/')),
            lookup=Lookup(),
            parent_queryset=self.parent_queryset,
        )

        assert handler.response.data == self.with_null_expected

    def test_handler_value_in_queryset_with_field_name(self, view):
        Article.objects.create(
            title='Test',
            category=Category.objects.create(
                name='Test',
                priority=CategoryPriority.LOW,
            ),
        )

        handler = self.handler_class(
            field=self.field_class(
                field_name='category__priority',
                choices=CategoryPriority.choices,
            ),
            view=view,
            request=Request(RequestFactory().get('/')),
            lookup=Lookup(),
            parent_queryset=self.parent_queryset,
        )

        assert handler.response.data == [
            {
                'id': CategoryPriority.LOW.value,
                'name': CategoryPriority.LOW.label,
            },
        ]

    def test_handler_value_in_queryset_custom_filter_negative(self, view):
        """Test choices with field not in the model.

        If field is not in the model, then just return choices.
        """
        handler = self.handler_class(
            field=self.field_class(
                field_name='not_exist', choices=[(1, 1), (2, 2)]
            ),
            view=view,
            request=Request(RequestFactory().get('/')),
            lookup=Lookup(),
            parent_queryset=self.parent_queryset,
        )

        assert handler.response.data == [
            {'id': 1, 'name': 1},
            {'id': 2, 'name': 2},
        ]

    @pytest.mark.parametrize(
        ('search', 'expected'),
        [
            (
                'News',
                [
                    {
                        'id': ArticleType.NEWS.value,
                        'name': ArticleType.NEWS.label,
                    }
                ],
            ),
            (
                'ne',
                [
                    {
                        'id': ArticleType.NEWS.value,
                        'name': ArticleType.NEWS.label,
                    }
                ],
            ),
            (
                'w',
                [
                    {
                        'id': ArticleType.NEWS.value,
                        'name': ArticleType.NEWS.label,
                    },
                    {
                        'id': ArticleType.REVIEW.value,
                        'name': ArticleType.REVIEW.label,
                    },
                ],
            ),
            ('not_exist', []),
        ],
    )
    def test_handler_with_search(self, view, search, expected):
        return self.run_test_handler_with_search(view, search, expected)


class TestMultipleChoiceFilter(TestChoiceFilter):
    field_class = django_filters.MultipleChoiceFilter


class TestBooleanFilter(HandlerTests):
    field_class = django_filters.BooleanFilter
    handler_class = LookupBooleanHandler
    expected = [
        {'id': 'true', 'name': 'Yes'},
    ]
    custom_serializer_expected = ['Yes']
    with_null_expected = [
        {'id': 'null', 'name': 'Unknown'},
        {'id': 'true', 'name': 'Yes'},
    ]
    field_kwargs = {'field_name': 'is_published'}
    field_custom_serializer = ChoiceCustomSerializer

    @property
    def parent_queryset(self) -> QuerySet[Article]:
        return Article.objects.all()

    @pytest.mark.parametrize(
        ('search', 'expected'),
        [
            (
                'Yes',
                [
                    {
                        'id': 'true',
                        'name': 'Yes',
                    }
                ],
            ),
            (
                'y',
                [
                    {
                        'id': 'true',
                        'name': 'Yes',
                    }
                ],
            ),
            ('not_exist', []),
        ],
    )
    def test_handler_with_search(self, view, search, expected):
        return self.run_test_handler_with_search(view, search, expected)


class TestChoiceField(HandlerTests):
    field_class = serializers.ChoiceField
    handler_class = LookupChoiceHandler
    expected = [
        {'id': 'news', 'name': 'News'},
        {'id': 'review', 'name': 'Review'},
        {'id': 'ad', 'name': 'Ad'},
    ]
    custom_serializer_expected = ArticleType.labels
    parent_queryset = None
    field_custom_serializer = ChoiceCustomSerializer

    @property
    def field_kwargs(self):
        return {'choices': ArticleType.choices, 'source': 'type_of'}

    @pytest.mark.parametrize(
        ('search', 'expected'),
        [
            (
                'News',
                [
                    {
                        'id': ArticleType.NEWS.value,
                        'name': ArticleType.NEWS.label,
                    }
                ],
            ),
            (
                'ne',
                [
                    {
                        'id': ArticleType.NEWS.value,
                        'name': ArticleType.NEWS.label,
                    }
                ],
            ),
            (
                'w',
                [
                    {
                        'id': ArticleType.NEWS.value,
                        'name': ArticleType.NEWS.label,
                    },
                    {
                        'id': ArticleType.REVIEW.value,
                        'name': ArticleType.REVIEW.label,
                    },
                ],
            ),
            ('not_exist', []),
        ],
    )
    def test_handler_with_search(self, view, search, expected):
        return self.run_test_handler_with_search(view, search, expected)


class TestMultipleChoiceField(TestChoiceField):
    field_class = serializers.MultipleChoiceField


class TestBooleanChoiceField(HandlerTests):
    field_class = serializers.BooleanField
    handler_class = LookupBooleanHandler
    expected = [
        {'id': 'true', 'name': 'Yes'},
        {'id': 'false', 'name': 'No'},
    ]
    with_null_expected = [
        {'id': 'null', 'name': 'Unknown'},
        {'id': 'true', 'name': 'Yes'},
        {'id': 'false', 'name': 'No'},
    ]
    custom_serializer_expected = ['Yes', 'No']
    field_kwargs = {'source': 'is_published'}
    field_custom_serializer = ChoiceCustomSerializer
    parent_queryset = None

    @pytest.mark.parametrize(
        ('search', 'expected'),
        [
            (
                'Yes',
                [
                    {
                        'id': 'true',
                        'name': 'Yes',
                    }
                ],
            ),
            (
                'y',
                [
                    {
                        'id': 'true',
                        'name': 'Yes',
                    }
                ],
            ),
            ('not_exist', []),
        ],
    )
    def test_handler_with_search(self, view, search, expected):
        return self.run_test_handler_with_search(view, search, expected)

    def test_handler_with_null_positive(self, view):
        Article.objects.create(title='Test', type_of=ArticleType.NEWS)
        Article.objects.create(title='Test', type_of=None, is_published=None)

        handler = self.handler_class(
            field=self.field_class(allow_null=True, **self.field_kwargs),
            view=view,
            request=Request(RequestFactory().get('/')),
            lookup=Lookup(),
            parent_queryset=self.parent_queryset,
        )

        assert handler.response.data == self.with_null_expected


class TestPrimaryKeyRelatedField(HandlerTests):
    field_class = serializers.PrimaryKeyRelatedField
    handler_class = LookupQuerySetHandler
    expected = [
        {'id': 1, 'name': 'First article'},
    ]
    custom_serializer_expected = ['First article']
    parent_queryset = None
    field_custom_serializer = ObjectCustomSerializer

    @property
    def field_kwargs(self):
        return {'queryset': Article.objects.all()}

    @pytest.mark.parametrize(
        ('search', 'expected'),
        [
            ('first', [{'id': 1, 'name': 'First article'}]),
            ('fi', [{'id': 1, 'name': 'First article'}]),
            (
                'ar',
                [
                    {'id': 2, 'name': 'Second article'},
                    {'id': 1, 'name': 'First article'},
                ],
            ),
            ('not_exist', []),
        ],
    )
    def test_handler_with_search(self, view, search, expected):
        Article.objects.create(title='First article')
        Article.objects.create(title='Second article')

        return self.run_test_handler_with_search(
            view, search, expected, lookup=Lookup(search_fields=['title'])
        )
