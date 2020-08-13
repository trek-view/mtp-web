from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.home, name='marketplace.home'),
    path('jobs/create', views.job_create, name='marketplace.job_create'),
    path('my-jobs/<str:unique_id>/edit/', views.job_edit, name='marketplace.my_job_edit'),
    re_path(r'^jobs/list/(?P<page>\d*)?$', views.job_list, name='marketplace.job_list'),
    re_path(r'^my-jobs/list/(?P<page>\d*)?$', views.my_job_list, name='marketplace.my_job_list'),
    path('my-jobs/<str:unique_id>/delete/', views.my_job_delete, name='marketplace.my_job_delete'),
    path('jobs/<str:unique_id>/apply/', views.job_apply, name='marketplace.job_apply'),
    path('jobs/<str:unique_id>/', views.job_detail, name='marketplace.job_detail'),
    path('ajax/get_job_detail/<str:unique_id>/', views.ajax_job_detail, name='marketplace.ajax_job_detail'),

    path('hire/create', views.photographer_create, name='marketplace.photographer_create'),
    path('hire/<str:unique_id>/edit/', views.photographer_edit, name='marketplace.my_photographer_edit'),
    re_path(r'^my-photographers/list/(?P<page>\d*)?$', views.my_photographer_list, name='marketplace.my_photographer_list'),
    re_path(r'^hire/list/(?P<page>\d*)?$', views.photographer_list, name='marketplace.photographer_list'),
    path('my-hire/<str:unique_id>/delete/', views.my_photographer_delete, name='marketplace.my_photographer_delete'),
    path('hire/contact/<str:unique_id>/', views.photographer_hire, name='marketplace.photographer_hire'),
    path('hire/<str:unique_id>/', views.photographer_detail, name='marketplace.photographer_detail'),
    path('ajax/get_photographer_detail/<str:unique_id>/', views.ajax_photographer_detail, name='marketplace.ajax_photographer_detail'),
]
