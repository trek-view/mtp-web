from django.urls import path, re_path
from . import views

urlpatterns = [

    path('capture/', views.index, name='challenge.index'),

    path('capture/create', views.challenge_create, name='challenge.challenge_create'),
    path('capture/<str:unique_id>/edit/', views.challenge_edit, name='challenge.my_challenge_edit'),
    path('capture/my-list/', views.my_challenge_list, name='challenge.my_challenge_list'),
    path('capture/list/', views.challenge_list, name='challenge.challenge_list'),
    path('capture/<str:unique_id>/delete/', views.my_challenge_delete, name='challenge.my_challenge_delete'),
    path('capture/<str:unique_id>/', views.challenge_detail, name='challenge.challenge_detail'),
    path('capture/<str:unique_id>/leaderboard/', views.challenge_leaderboard, name='challenge.challenge_leaderboard'),
    path('capture/ajax/get_challenge_detail/<str:unique_id>/', views.ajax_challenge_detail, name='challenge.ajax_challenge_detail'),

    path('label/create', views.label_challenge_create, name='challenge.label_challenge_create'),
    path('label/<str:unique_id>/edit/', views.label_challenge_edit, name='challenge.my_label_challenge_edit'),
    path('label/my-list/', views.my_label_challenge_list, name='challenge.my_label_challenge_list'),
    path('label/list/', views.label_challenge_list, name='challenge.label_challenge_list'),
    path('label/<str:unique_id>/delete/', views.my_label_challenge_delete, name='challenge.my_label_challenge_delete'),
    path('label/<str:unique_id>/', views.label_challenge_detail, name='challenge.label_challenge_detail'),
    path('label/<str:unique_id>/leaderboard/', views.label_challenge_leaderboard, name='challenge.label_challenge_leaderboard'),
    path('label/ajax/get_challenge_detail/<str:unique_id>/', views.ajax_label_challenge_detail, name='challenge.ajax_label_challenge_detail'),
]
