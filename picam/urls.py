from django.urls import path
from . import views

urlpatterns = [
    path('picam/', views.picam, name='picam'),
    path('picam/data/', views.picam_data, name='picam_data'),  # JSON 데이터 반환 API
    path('picam/toggle/', views.toggle_detection, name='toggle_detection'),  # JSON 데이터 반환 API
    path('webcam/', views.webcam, name='webcam'),
    path('detect/', views.webcam_detect_objects, name='webcam_detect_objects'),
    path('status/', views.system_status, name='system_status'),
]
