import django_filters
from django_filters import NumberFilter

from tests.app.models import Article, ArticleType, Category, Tag


class ArticleFilterSet(django_filters.FilterSet):
    id = NumberFilter(lookup_expr='iexact')
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.published(),
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.published(),
    )
    type_of = django_filters.ChoiceFilter(
        choices=[
            (x.value, x.label)
            for x in ArticleType
            if x.value != ArticleType.AD
        ],
    )

    class Meta:
        model = Article
        fields = (
            'category',
            'tags',
            'type_of',
        )


class CustomListArticleFilterSet(django_filters.FilterSet):
    type_of = django_filters.ChoiceFilter(
        choices=[(ArticleType.AD.value, ArticleType.AD.label)],
    )

    class Meta:
        model = Article
        fields = ('type_of',)


class CategoryFilterSet(django_filters.FilterSet):
    class Meta:
        model = Category
        fields = (
            'is_public',
            'priority',
            'author',
        )
