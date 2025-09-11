"""
URL configuration for Project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path
from .import views as v
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', v.Index, name='index'),
    path('home', v.Home, name='home'),
    path('logout', v.logoutUser, name='logout'),
    path('send-request/<int:user_id>/', v.send_request, name='send_request'),
    path('respond-request/<int:req_id>/', v.respond_request, name='respond_request'),
    path("like/<int:post_id>/", v.like_post, name="like_post"),
    path("comment/<int:post_id>/", v.add_comment, name="add_comment"),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
