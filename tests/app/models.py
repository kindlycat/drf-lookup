from django.conf import settings
from django.db import models
from django.db.models import TextChoices


class PublicQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_public=True)


class Tag(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    is_public = models.BooleanField(default=True)

    objects = PublicQuerySet.as_manager()

    class Meta:
        verbose_name = 'tag'
        verbose_name_plural = 'tags'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class CategoryPriority(TextChoices):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'


class Category(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    is_public = models.BooleanField(default=True)
    priority = models.CharField(
        max_length=10,
        choices=CategoryPriority.choices,
        default=CategoryPriority.LOW,
    )
    author = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
    )

    objects = PublicQuerySet.as_manager()

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class ArticleType(TextChoices):
    NEWS = 'news'
    REVIEW = 'review'
    AD = 'ad'


class Article(models.Model):
    title = models.CharField(max_length=100, db_index=True)
    type_of = models.CharField(
        max_length=10,
        choices=ArticleType.choices,
        default=ArticleType.NEWS,
        null=True,
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)
    is_published = models.BooleanField(default=True, null=True)
    tags = models.ManyToManyField(Tag)

    class Meta:
        verbose_name = 'news'
        verbose_name_plural = 'news'
        ordering = ['-pk']

    def __str__(self) -> str:
        return self.title
