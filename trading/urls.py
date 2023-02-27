from django.urls import path
from . import views

urlpatterns = [
    path('my-page/', views.my_view, name='my-page'),
]