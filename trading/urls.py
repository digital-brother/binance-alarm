from django.urls import path
from .views import my_view, register

urlpatterns = [
    path('my-page/', my_view, name='my-page'),
    path('register/', register, name='register'),
]