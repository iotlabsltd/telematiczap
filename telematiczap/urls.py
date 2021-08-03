"""telematics URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.urls import include, path
import oauth2_provider.views as oauth2_views
from django.conf import settings
import main.views as views
from django.contrib import admin
from django.conf.urls.static import static

oauth2_endpoint_views = [
    path('authorize/', oauth2_views.AuthorizationView.as_view(), name="authorize"),
    path('token/', oauth2_views.TokenView.as_view(), name="token"),
    path('revoke-token/', oauth2_views.RevokeTokenView.as_view(), name="revoke-token"),
]

if settings.DEBUG:
    # OAuth2 Application Management endpoints
    oauth2_endpoint_views += [
        path('applications/', oauth2_views.ApplicationList.as_view(), name="list"),
        path('applications/register/', oauth2_views.ApplicationRegistration.as_view(), name="register"),
        path('applications/<pk>/', oauth2_views.ApplicationDetail.as_view(), name="detail"),
        path('applications/<pk>/delete/', oauth2_views.ApplicationDelete.as_view(), name="delete"),
        path('applications/<pk>/update/', oauth2_views.ApplicationUpdate.as_view(), name="update"),
    ]

    # OAuth2 Token Management endpoints
    oauth2_endpoint_views += [
        path('authorized-tokens/', oauth2_views.AuthorizedTokensListView.as_view(), name="authorized-token-list"),
        path('authorized-tokens/<pk>/delete/', oauth2_views.AuthorizedTokenDeleteView.as_view(),
            name="authorized-token-delete"),
    ]


urlpatterns = [
    path('admin/', admin.site.urls),
    #path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('o/', include((oauth2_endpoint_views, 'oauth2_provider'), namespace="oauth2_provider")),
    #path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/hello', views.ApiEndpoint.as_view()),  # an example resource endpoint
    path("", views.HomeFormView.as_view(), name="home"),
    path("contact", views.ContactFormView.as_view(), name="contact"),
    path('', include('django.contrib.auth.urls')),
    path("register", views.RegisterFormView.as_view(), name="register"),
    path("data-before", views.DataBeforeList.as_view(), name="data-before"),
    path("data-before/<pk>", views.DataBeforeRUD.as_view()),
    path("data-after", views.DataAfterList.as_view(), name="data-after"),
    path("data-after/<pk>", views.DataAfterRUD.as_view()),
    path("data-format", views.DataFormatList.as_view(), name="data-format"),
    path("data-format/<pk>", views.DataFormatRUD.as_view()),
]

if settings.DEBUG: 
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
