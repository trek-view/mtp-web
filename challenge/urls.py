from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.index, name='challenge.index'),

    path('create', views.challenge_create, name='challenge.challenge_create'),
    path('<str:unique_id>/edit/', views.challenge_edit, name='challenge.my_challenge_edit'),
    path('my-list/', views.my_challenge_list, name='challenge.my_challenge_list'),
    path('list/', views.challenge_list, name='challenge.challenge_list'),
    path('<str:unique_id>/delete/', views.my_challenge_delete, name='challenge.my_challenge_delete'),
    path('<str:unique_id>/', views.challenge_detail, name='challenge.challenge_detail'),
    path('<str:unique_id>/leaderboard/', views.challenge_leaderboard, name='challenge.challenge_leaderboard'),
    path('ajax/get_challenge_detail/<str:unique_id>/', views.ajax_challenge_detail, name='challenge.ajax_challenge_detail'),
]
