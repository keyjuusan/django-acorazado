from django.db import router
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from usuarios.views import GroupViewSet, UserViewSet

router = DefaultRouter() # noqa
router.register(r"usuarios",UserViewSet)
router.register(r"grupos",GroupViewSet)

urlpatterns = [
    path("",include(router.urls))
]