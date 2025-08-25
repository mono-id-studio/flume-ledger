from django.contrib import admin
from django.urls import path, URLPattern, URLResolver
from django.conf import settings
from django.conf.urls.static import static
from typing import List, Union

from app.routes.routes import v1


urlpatterns: List[Union[URLPattern, URLResolver]] = [
    path("admin/", admin.site.urls),
    path("api/", v1.urls),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
