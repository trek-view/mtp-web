from django.urls import path, re_path
from . import views

urlpatterns = [
    path('home', views.home, name='home'),
    path('', views.home, name='guidebook.home'),

    path('create', views.guidebook_create, name='guidebook.create'),
    path('<str:unique_id>/edit/', views.guidebook_create, name='guidebook.guidebook_edit'),
    re_path(r'^list/(?P<page>\d*)?$', views.guidebook_list, name='guidebook.guidebook_list'),
    re_path(r'^my-guidebook-list/(?P<page>\d*)?$', views.my_guidebook_list, name='guidebook.my_guidebook_list'),
    path('<str:unique_id>/detail/', views.guidebook_detail, name='guidebook.guidebook_detail'),
    path('<str:unique_id>/check_like/', views.check_like, name='guidebook.check_like'),
    path('<str:unique_id>/check_publish/', views.check_publish, name='guidebook.check_publish'),
    path('<str:unique_id>/delete/', views.guidebook_delete, name='guidebook.guidebook_delete'),

    path('<str:unique_id>/scene/', views.add_scene, name='guidebook.add_scene'),
    path('<str:unique_id>/ajax/save_scene/', views.ajax_add_scene, name='guidebook.ajax_add_scene'),
    path('<str:unique_id>/ajax/upload_file/', views.ajax_upload_file, name='guidebook.ajax_upload_file'),
    path('<str:unique_id>/ajax/guidebook_update/', views.ajax_guidebook_update, name='guidebook.ajax_guidebook_update'),
    path('<str:unique_id>/ajax/order_scene/', views.ajax_order_scene, name='guidebook.ajax_order_scene'),
    path('<str:unique_id>/scene/ajax/save_poi/<int:pk>/', views.ajax_save_poi, name='guidebook.ajax_save_poi'),
    path('<str:unique_id>/scene/ajax/delete_poi/<int:pk>/', views.ajax_delete_poi, name='guidebook.ajax_delete_poi'),
    path('<str:unique_id>/scene/ajax/delete_scene/<int:pk>/', views.ajax_delete_scene, name='guidebook.ajax_delete_scene'),
    path('<str:unique_id>/ajax/edit/get_scene/', views.ajax_get_edit_scene, name='guidebook.ajax_get_edit_scene'),
    path('<str:unique_id>/ajax/get_scene/', views.ajax_get_scene, name='guidebook.ajax_get_scene'),
    path('<str:unique_id>/ajax/get_scene_list/', views.ajax_get_scene_list, name='guidebook.ajax_get_scene_list'),

    # path('jobs/create', views.job_create, name='marketplace.job_create'),
    # path('jobs/jobs/detail/<str:unique_id>/', views.job_detail, name='marketplace.job_detail'),
    # path('my-jobs/<str:unique_id>/edit/', views.job_edit, name='marketplace.my_job_edit'),
    # re_path(r'^jobs/list/(?P<page>\d*)?$', views.job_list, name='marketplace.job_list'),
    # re_path(r'^my-jobs/list/(?P<page>\d*)?$', views.my_job_list, name='marketplace.my_job_list'),
    # path('my-jobs/<str:unique_id>/delete/', views.my_job_delete, name='marketplace.my_job_delete'),
    # path('jobs/apply/<str:unique_id>/', views.job_apply, name='marketplace.job_apply'),
    # path('ajax/get_job_detail/<str:unique_id>/', views.ajax_job_detail, name='marketplace.ajax_job_detail'),

    # path('hire/create', views.photographer_create, name='marketplace.photographer_create'),
    # path('hire/detail/<str:unique_id>/', views.photographer_detail, name='marketplace.photographer_detail'),
    # path('hire/<str:unique_id>/edit/', views.photographer_edit, name='marketplace.my_photographer_edit'),
    # re_path(r'^my-photographers/list/(?P<page>\d*)?$', views.my_photographer_list, name='marketplace.my_photographer_list'),
    # re_path(r'^hire/list/(?P<page>\d*)?$', views.photographer_list, name='marketplace.photographer_list'),
    # path('my-hire/<str:unique_id>/delete/', views.my_photographer_delete, name='marketplace.my_photographer_delete'),
    # path('hire/contact/<str:unique_id>/', views.photographer_hire, name='marketplace.photographer_hire'),
    # path('ajax/get_photographer_detail/<str:unique_id>/', views.ajax_photographer_detail, name='marketplace.ajax_photographer_detail'),
]
