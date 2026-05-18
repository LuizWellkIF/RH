from rest_framework.routers import DefaultRouter
from .views import SolicitacaoFeriasViewSet

router = DefaultRouter()
router.register(r'', SolicitacaoFeriasViewSet, basename='ferias')

urlpatterns = router.urls