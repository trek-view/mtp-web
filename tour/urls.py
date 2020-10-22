from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.index, name='tour.index'),
    path('create', views.tour_create, name='tour.tour_create'),
    path('list', views.tour_list, name='tour.tour_list'),
    path('my-tour-list', views.my_tour_list, name='tour.my_tour_list'),
    path('<str:unique_id>/detail', views.tour_detail, name='tour.tour_detail'),
    path('<str:unique_id>/delete', views.tour_delete, name='tour.tour_delete'),
    path('<str:unique_id>/add-seq', views.tour_add_sequence, name='tour.tour_add_sequence'),
    path('<str:unique_id>/ajax_change_tour_seq', views.ajax_change_tour_seq, name='tour.ajax_change_tour_seq'),
    path('<str:unique_id>/ajax_order_sequence', views.ajax_order_sequence, name='tour.ajax_order_sequence'),
    path('<str:unique_id>/ajax_tour_check_publish', views.ajax_tour_check_publish, name='tour.ajax_tour_check_publish'),
    path('<str:unique_id>/ajax_tour_check_like', views.ajax_tour_check_like, name='tour.ajax_tour_check_like'),
    path('<str:unique_id>/ajax_tour_update', views.ajax_tour_update, name='tour.ajax_tour_update'),
    path('<str:unique_id>/ajax_get_detail/', views.ajax_get_detail, name='tour.ajax_get_detail'),
    # path('<str:unique_id>/ajax_sequence/', views.ajax_get_detail, name='tour.ajax_get_detail'),

    path('ajax_get_detail_by_image_key/<str:image_key>', views.ajax_get_detail_by_image_key, name='tour.ajax_get_detail_by_image_key'),
]
