from django.urls import path
from django.contrib.auth import views as auth_views
from . import views 

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='hunt/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('add-area/', views.add_area, name='add_area'),
    path('delete-area/<int:pk>/', views.delete_area, name='delete_area'),
    path('forecast/<int:pk>/', views.area_forecast, name='area_forecast'),
]