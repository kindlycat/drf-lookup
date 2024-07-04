from rest_framework import serializers

from tests.app.models import Article, ArticleType, Category, Tag


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = (
            'id',
            'title',
            'category',
            'type_of',
            'tags',
        )
        extra_kwargs = {
            'category': {'queryset': Category.objects.published()},
            'tags': {'queryset': Tag.objects.published()},
            'type_of': {
                'choices': [
                    (x.value, x.label)
                    for x in ArticleType
                    if x.value != ArticleType.AD
                ],
            },
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # For update tests
        if self.instance and self.instance.pk:
            self.fields['category'].queryset = Category.objects.filter(
                id=self.instance.category_id
            )


class ArticleCustomCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = (
            'id',
            'title',
            'category',
            'type_of',
            'tags',
        )
        extra_kwargs = {
            'type_of': {
                'choices': [
                    (ArticleType.AD.value, ArticleType.AD.label),
                ],
            },
        }
