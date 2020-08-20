from django.urls import path, re_path
from . import views

urlpatterns = [
    # Sequence

    path('', views.index, name='sequence.index'),
    path('sequence/sequence-list', views.sequence_list, name='sequence.sequence_list'),
    path('sequence/my-sequence-list', views.my_sequence_list, name='sequence.my_sequence_list'),
    path('sequence/<str:unique_id>/detail', views.sequence_detail, name='sequence.sequence_detail'),
    path('sequence/<str:unique_id>/delete', views.sequence_delete, name='sequence.sequence_delete'),

    path('sequence/<str:unique_id>/ajax_save_sequence', views.ajax_save_sequence, name='sequence.ajax_save_sequence'),
    path('sequence/<str:unique_id>/ajax_sequence_check_publish', views.ajax_sequence_check_publish, name='sequence.ajax_sequence_check_publish'),
    path('sequence/<str:unique_id>/ajax_sequence_check_like', views.ajax_sequence_check_like, name='sequence.ajax_sequence_check_like'),

    path('sequence/transport-sequence-list', views.transport_sequence_list, name='sequence.transport_sequence_list'),
    path('sequence/transport', views.ajax_transport, name='sequence.ajax_transport'),

    # Tour

    path('tour/create', views.tour_create, name='sequence.tour_create'),
    path('tour/tour-list', views.tour_list, name='sequence.tour_list'),
    path('tour/my-tour-list', views.my_tour_list, name='sequence.my_tour_list'),
    path('tour/<str:unique_id>/detail', views.tour_detail, name='sequence.tour_detail'),
    path('tour/<str:unique_id>/delete', views.tour_delete, name='sequence.tour_delete'),
    path('tour/<str:unique_id>/add-seq', views.tour_add_sequence, name='sequence.tour_add_sequence'),
    path('tour/<str:unique_id>/ajax_change_tour_seq', views.ajax_change_tour_seq, name='sequence.ajax_change_tour_seq'),
    path('tour/<str:unique_id>/ajax_order_sequence', views.ajax_order_sequence, name='sequence.ajax_order_sequence'),
    path('tour/<str:unique_id>/ajax_tour_check_publish', views.ajax_tour_check_publish, name='sequence.ajax_tour_check_publish'),
    path('tour/<str:unique_id>/ajax_tour_check_like', views.ajax_tour_check_like, name='sequence.ajax_tour_check_like'),
    path('tour/<str:unique_id>/ajax_tour_update', views.ajax_tour_update, name='sequence.ajax_tour_update'),
]
