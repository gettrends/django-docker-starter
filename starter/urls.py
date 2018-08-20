"""starter URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path, include
from accounts.urls import router
from rest_framework_jwt.views import verify_jwt_token, obtain_jwt_token

from accounts.views import ConfirmUserViewSet, PasswordChangeRequestViewSet, PasswordChangeViewSet

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^v1/verify/', verify_jwt_token),
    url(r'^v1/auth/', obtain_jwt_token),
    url(r'^v1/request_password_change/', PasswordChangeRequestViewSet.as_view({'post': 'create'})),
    url(r'^v1/change_password/', PasswordChangeViewSet),
    url(r'^v1/confirm/', ConfirmUserViewSet),
    url(r'^v1/', include((router.urls, 'accounts'), namespace='accounts')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
