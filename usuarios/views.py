from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import Group, User
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator

from usuarios.serializers import GroupSerializer, UserSerializer

@method_decorator(csrf_protect, name="dispatch")
class UserViewSet(ModelViewSet):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class GroupViewSet(ModelViewSet):
    queryset = Group.objects.all().order_by("name")
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]