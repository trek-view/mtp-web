from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.index, name='photographer.index'),

    path('create', views.photographer_create, name='photographer.photographer_create'),
    path('<str:unique_id>/edit/', views.photographer_edit, name='photographer.my_photographer_edit'),
    re_path(r'^my-list/(?P<page>\d*)?$', views.my_photographer_list, name='photographer.my_photographer_list'),
    re_path(r'^list/(?P<page>\d*)?$', views.photographer_list, name='photographer.photographer_list'),
    path('<str:unique_id>/delete/', views.my_photographer_delete, name='photographer.my_photographer_delete'),
    path('contact/<str:unique_id>/', views.photographer_hire, name='photographer.photographer_hire'),
    path('<str:unique_id>/', views.photographer_detail, name='photographer.photographer_detail'),
    path('ajax/get_photographer_detail/<str:unique_id>/', views.ajax_photographer_detail, name='photographer.ajax_photographer_detail'),
]
