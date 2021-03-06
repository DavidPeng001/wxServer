"""wxServer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from api import views

urlpatterns = [
    url(r'^api/search/', views.keyword_search_api),
    url(r'^api/searchinfo/', views.info_search_api),
    url(r'^admin/', views.connection_test),
    url(r'^api/login/', views.login),
    url(r'^api/captchaupdate/', views.update_captcha),
    url(r'^api/login/captcha/', views.login_with_captcha),
    url(r'^api/quicklogin/', views.quick_login),
    url(r'^api/roomsearch/', views.room_search),
    url(r'^api/roombooking/', views.room_booking),
    url(r'^api/renew/',views.book_renew),
    url(r'^api/renew/captcha/',views.book_renew_with_captcha),
    url(r'^api/renewsearch/', views.book_renew_search),
    url(r'^api/renewsearch/captcha/', views.book_renew_search_with_captcha),

    # warning: url mapping below should NOT be enabled in server
    # url(r'^api/crontest/', views.save_room_table)

]
