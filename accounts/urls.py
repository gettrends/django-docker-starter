from __future__ import absolute_import, print_function, unicode_literals

from rest_framework import routers
from . import views

DEFAULT = {'get': 'list'}

router = routers.SimpleRouter()

# router.register('auth', views.VerifyViewSet.as_view())
router.register('register', views.RegisterViewSet, base_name='register')
router.register('user', views.UserViewSet)
# router.register('confirm', views.ConfirmUserViewSet)
# router.register('request_password_change', views.PasswordChangeRequestViewSet)
# router.register('change_password', views.PasswordChangeViewSet)

urlpatterns = router.urls
