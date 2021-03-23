from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='sequence.index'),
    path('list', views.sequence_list, name='sequence.sequence_list'),
    path('my-sequence-list', views.my_sequence_list, name='sequence.my_sequence_list'),

    path('photo', views.image_leaderboard, name='sequence.image_leaderboard'),
    path('ajax_add_label_type', views.ajax_add_label_type, name='sequence.ajax_add_label_type'),

    path('<str:unique_id>/detail', views.sequence_detail, name='sequence.sequence_detail'),
    path('<str:unique_id>/delete', views.sequence_delete, name='sequence.sequence_delete'),

    path('<str:unique_id>/tour/<str:tour_id>', views.tour_sequence_detail, name='sequence.tour_sequence_detail'),

    path('<str:unique_id>/ajax_save_sequence', views.ajax_save_sequence, name='sequence.ajax_save_sequence'),
    path('<str:unique_id>/ajax_sequence_check_publish', views.ajax_sequence_check_publish, name='sequence.ajax_sequence_check_publish'),
    path('<str:unique_id>/ajax_sequence_check_like', views.ajax_sequence_check_like, name='sequence.ajax_sequence_check_like'),
    path('<str:unique_id>/ajax_get_image_list/', views.ajax_get_image_list, name='sequence.ajax_get_image_list'),
    path('<str:unique_id>/ajax_get_image_ele/', views.ajax_get_image_ele, name='sequence.ajax_get_image_ele'),
    path('<str:unique_id>/ajax_get_detail/', views.ajax_get_detail, name='sequence.ajax_get_detail'),
    path('<str:unique_id>/ajax_image_map_feature/', views.ajax_image_map_feature, name='sequence.ajax_image_map_feature'),
    path('<str:unique_id>/ajax_get_image_gpx_data/', views.ajax_get_image_gpx_data,
         name='sequence.ajax_get_image_gpx_data'),

    path('<str:unique_id>/ajax_add_in_tour/', views.ajax_add_in_tour, name='sequence.ajax_add_in_tour'),

    path('<str:seq_key>/ajax_import/', views.ajax_import, name='sequence.ajax_import'),
    path('<str:unique_id>/ajax_reimport', views.ajax_reimport, name='sequence.ajax_reimport'),

    path('<str:unique_id>/ajax_image_mark_view/<str:image_key>/', views.ajax_image_mark_view, name='sequence.ajax_image_mark_view'),
    path('<str:unique_id>/ajax_get_image_detail/<str:image_key>/', views.ajax_get_image_detail, name='sequence.ajax_get_image_detail'),
    path('<str:unique_id>/ajax_add_image_label/<str:image_key>/', views.ajax_add_image_label, name='sequence.ajax_add_image_label'),
    path('<str:unique_id>/ajax_get_image_label/<str:image_key>/', views.ajax_get_image_label, name='sequence.ajax_get_image_label'),
    path('<str:unique_id>/ajax_delete_image_label/<str:image_key>/', views.ajax_delete_image_label, name='sequence.ajax_delete_image_label'),

    path('ajax_get_detail_by_image_key/<str:image_key>', views.ajax_get_detail_by_image_key, name='sequence.ajax_get_detail_by_image_key'),

    path('import-sequence-list', views.import_sequence_list, name='sequence.import_sequence_list'),
    path('import-sequence', views.import_sequence, name='sequence.import_sequence'),

    path('manual_update', views.manual_update, name='sequence.manual_update'),


    path('ajax_get_map_features/', views.ajax_get_map_features, name='sequence.ajax_get_map_features'),
    path('ajax_get_import_sequences/', views.ajax_get_import_sequences, name='sequence.ajax_get_import_sequences'),
    path('ajax_get_import_sequence/', views.ajax_get_import_sequence, name='sequence.ajax_get_import_sequence'),
    path('ajax_get_import_next_sequence_id/', views.ajax_get_import_next_sequence_id, name='sequence.ajax_get_import_next_sequence_id'),
    path('ajax_check_import_limit/', views.ajax_check_import_limit, name='sequence.ajax_check_import_limit'),
]
