from __future__ import absolute_import, print_function, unicode_literals

from rest_framework import routers
from . import views

router = routers.SimpleRouter()

router.register('register', views.RegisterViewSet, base_name='register')
router.register('user', views.UserViewSet)

urlpatterns = router.urls
