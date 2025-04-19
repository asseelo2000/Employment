"""
URL configuration for Core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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

from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from Employment.admin import admin_site
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin_site.urls),
    path("select2/", include("django_select2.urls")),
    path("chaining/", include("smart_selects.urls")),
    path("employment/", include("Employment.urls", namespace="employment")),  # Dashboard URLs
    path('helpdesk/', include('helpdesk.urls')),
    path("teams/", include("pinax.teams.urls", namespace="pinax_teams")),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
