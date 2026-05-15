from rest_framework.routers import DefaultRouter
from .views import RegistroPontoViewSet

router = DefaultRouter()
router.register(r'', RegistroPontoViewSet, basename='ponto')

urlpatterns = router.urls