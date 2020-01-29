from django.urls import path
from . import views
urlpatterns = [
    path('login/', views.loginpage, name='loginpage'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout, name='logout'),
    path('signup/', views.signup, name='signup'),
]
