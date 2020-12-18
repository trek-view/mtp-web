from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.home, name='guidebook.home'),
    path('create', views.guidebook_create, name='guidebook.create'),
    path('<str:unique_id>/edit/', views.guidebook_create, name='guidebook.guidebook_edit'),
    path('list/', views.guidebook_list, name='guidebook.guidebook_list'),
    path('my-guidebook-list/', views.my_guidebook_list, name='guidebook.my_guidebook_list'),
    path('<str:unique_id>/detail/', views.guidebook_detail, name='guidebook.guidebook_detail'),
    path('<str:unique_id>/check_like/', views.check_like, name='guidebook.check_like'),
    path('<str:unique_id>/check_publish/', views.check_publish, name='guidebook.check_publish'),
    path('<str:unique_id>/delete/', views.guidebook_delete, name='guidebook.guidebook_delete'),

    path('<str:unique_id>/scene/', views.add_scene, name='guidebook.add_scene'),
    path('<str:unique_id>/ajax/save_scene/', views.ajax_add_scene, name='guidebook.ajax_add_scene'),
    path('<str:unique_id>/ajax_get_detail/', views.ajax_get_detail, name='guidebook.ajax_get_detail'),
    path('<str:unique_id>/ajax/upload_file/', views.ajax_upload_file, name='guidebook.ajax_upload_file'),
    path('<str:unique_id>/ajax/guidebook_update/', views.ajax_guidebook_update, name='guidebook.ajax_guidebook_update'),
    path('<str:unique_id>/ajax/order_scene/', views.ajax_order_scene, name='guidebook.ajax_order_scene'),

    path('<str:unique_id>/scene/ajax/save_poi/<int:pk>/', views.ajax_save_poi, name='guidebook.ajax_save_poi'),
    path('<str:unique_id>/scene/ajax/delete_poi/<int:pk>/', views.ajax_delete_poi, name='guidebook.ajax_delete_poi'),
    path('<str:unique_id>/scene/ajax/add_external_url/<int:pk>/', views.ajax_add_external_url, name='guidebook.ajax_add_external_url'),
    path('<str:unique_id>/scene/ajax/delete_external_url/<int:pk>/', views.ajax_delete_external_url, name='guidebook.ajax_delete_external_url'),
    path('<str:unique_id>/scene/ajax/delete_scene/<int:pk>/', views.ajax_delete_scene, name='guidebook.ajax_delete_scene'),

    path('<str:unique_id>/ajax/edit/get_scene/', views.ajax_get_edit_scene, name='guidebook.ajax_get_edit_scene'),
    path('<str:unique_id>/ajax/edit/set_starting_view/', views.ajax_set_start_view, name='guidebook.ajax_set_start_view'),
    path('<str:unique_id>/ajax/get_scene/', views.ajax_get_scene, name='guidebook.ajax_get_scene'),
    path('<str:unique_id>/ajax/get_scene_list/', views.ajax_get_scene_list, name='guidebook.ajax_get_scene_list'),

    path('ajax_get_detail_by_image_key/<str:image_key>', views.ajax_get_detail_by_image_key, name='guidebook.ajax_get_detail_by_image_key'),

    path('<str:unique_id>/scene/ajax_upload_scene_image/<str:scene_id>', views.ajax_upload_scene_image, name='guidebook.ajax_upload_scene_image'),
    path('<str:unique_id>/scene/ajax_upload_scene_video/<str:scene_id>', views.ajax_upload_scene_video, name='guidebook.ajax_upload_scene_video'),
    path('<str:unique_id>/scene/<str:scene_id>/ajax_upload_poi_image/<str:poi_id>', views.ajax_upload_poi_image, name='guidebook.ajax_upload_poi_image'),
    path('<str:unique_id>/scene/<str:scene_id>/ajax_upload_poi_video/<str:poi_id>', views.ajax_upload_poi_video,
         name='guidebook.ajax_upload_poi_video'),

]
