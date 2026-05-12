from rest_framework.routers import DefaultRouter
from .views import DepartamentoViewSet

router = DefaultRouter()
router.register(r'', DepartamentoViewSet, basename='departamentos')

urlpatterns = router.urls