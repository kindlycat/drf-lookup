from rest_framework.routers import SimpleRouter

from tests.app.views import ArticleViewSet


router = SimpleRouter()
router.register('articles', ArticleViewSet)


urlpatterns = router.urls
