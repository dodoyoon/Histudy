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

from photos.views import detail
from photos.views import upload, photoList, homepage, allList, main, delete_data, confirm_delete
from django.urls import include
from django.urls import path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


urlpatterns = [
    url(r'^photos/(?P<pk>[0-9]+)/$', detail, name='detail'),
    url(r'^photos/upload/$', upload, name='upload'),
    url(r'^list/', photoList, name='list'),
    url(r'^all/', allList, name='all_list'),
    url(r'^home/', homepage, name='home'),
    url(r'^admin/', admin.site.urls),
    path('', main, name='main'),
    path('', include('photos.urls')),
    url(r'^delete_data/(?P<pk>\d+)$', delete_data, name='delete_data'),
    url(r'^delete_confirm/(?P<pk>\d+)$', confirm_delete, name='confirm_delete'),
]

urlpatterns += static('/upload_files/', document_root=settings.MEDIA_ROOT)

#Add Django site authentication urls (for login, logout, password management)
urlpatterns += [
    path('accounts/', include('photos.urls')),
]

urlpatterns += staticfiles_urlpatterns()
