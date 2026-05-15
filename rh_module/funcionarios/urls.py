from rest_framework.routers import DefaultRouter
from .views import FuncionarioViewSet

router = DefaultRouter()
router.register(r'', FuncionarioViewSet, basename='funcionarios')

urlpatterns = router.urls