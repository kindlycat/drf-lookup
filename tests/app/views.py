from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from drf_lookup.views import LookupMixin
from tests.app.filters import ArticleFilterSet, CustomListArticleFilterSet
from tests.app.models import Article
from tests.app.serializers import (
    ArticleCustomCreateSerializer,
    ArticleSerializer,
)


class ArticleViewSet(LookupMixin, viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    filterset_class = ArticleFilterSet
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]

    @action(detail=False, filterset_class=CustomListArticleFilterSet)
    def custom_list(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @action(detail=False, serializer_class=ArticleCustomCreateSerializer)
    def custom_create(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
