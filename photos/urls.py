from django.urls import path
from django.conf.urls import url
from . import views

urlpatterns = [
    path('login/', views.loginpage, name='loginpage'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('popup/', views.popup, name='popup'),
    url(r'^password/$', views.change_password, name='change_password'),
    path('add_member/', views.add_member, name='add_member'),
]
