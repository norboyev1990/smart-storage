"""
URL configuration for smart_storage project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.views import ProductViewSet
from reports.views import RemainingItemsView, SoldItemsView
from users.views import TelegramUserViewSet

router = DefaultRouter()
router.register(r'users', TelegramUserViewSet)
router.register(r'products', ProductViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/reports/remaining/', RemainingItemsView.as_view(), name='report-remaining'),
    path('api/reports/sold/', SoldItemsView.as_view(), name='report-sold'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
