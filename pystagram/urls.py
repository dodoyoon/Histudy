"""pystagram URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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

from django.conf.urls import url
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings

from photos.views import detail, announce_write, announce_detail, confirm_delete_announce, confirm_delete_member, confirm_delete_user
from photos.views import csv_upload, photoList, main, confirm_delete_data, userList, announce, inquiry, data_edit
from photos.views import data_upload, top3, group_profile, rank
from django.urls import include
from django.urls import path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.static import serve

urlpatterns = [
    url(r'^photos/(?P<pk>[0-9]+)/$', detail, name='detail'),
    url(r'^photos/csv_upload/$', csv_upload, name='csv_upload'),
    url(r'^user/', userList, name='userList'),
    url(r'^announce/write/$', announce_write, name='announce_write'),
    url(r'^announce/(?P<pk>[0-9]+)/$', announce_detail, name='announce_detail'),
    url(r'^announce/', announce, name='announce'),
    url(r'^admin/', admin.site.urls),
    path('', main, name='main'),
    path('', include('photos.urls')),
    url(r'^delete_confirm/(?P<pk>\d+)$', confirm_delete_data, name='confirm_delete_data'),
    url(r'^announce_delete_confirm/(?P<pk>\d+)$', confirm_delete_announce, name='confirm_delete_announce'),
    url(r'^member_delete_confirm/(?P<pk>\d+)$', confirm_delete_member, name='confirm_delete_member'),
    url(r'^list/(?P<user>\w+)$', photoList, name='list'),
    url(r'^rank/$', rank, name='rank'),
    url(r'^profile/(?P<user>\w+)$', group_profile, name='group_profile'),
    url(r'^user_delete_confirm/(?P<pk>\d+)$', confirm_delete_user, name='confirm_delete_user'),
    url(r'^inquiry/$', inquiry, name='inquiry'),
    url(r'^upload/$', data_upload, name='upload'),
    url(r'^top3/$', top3, name='top3'),
    url(r'^summernote/', include('django_summernote.urls')),
    url(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
    url(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
    url(r'^photos/(?P<pk>[0-9]+)/edit', data_edit, name='edit'),
]

urlpatterns += static('/upload_files/', document_root=settings.MEDIA_ROOT)

#Add Django site authentication urls (for login, logout, password management)
urlpatterns += [
    path('accounts/', include('photos.urls')),
]

urlpatterns += staticfiles_urlpatterns()
