from django.urls import path
from . import views
from fileupload import views as ful_views


urlpatterns = [
    path('', views.index),
    path('samples/<int:num_page>/', views.pages_view, name='pages_view'),
    path('sub/<int:n_page>/<int:n_sect>/', views.sub_view, name='sub_view'),
    path('sensor/', views.sensor, name='sensor'),
    path('tensor/', views.tensor, name='tensor'),
]