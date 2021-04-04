from django.urls import path

from . import views

app_name = 'posts'

urlpatterns = [
    path('', views.IndexListView.as_view(), name='index'),
    path('group/<slug:slug>/',
         views.GroupDetailView.as_view(), name='group_posts'),
    path('new/', views.new_post, name='new_post'),
    path('follow/', views.follow_index, name='follow_index'),
    path('<str:username>/follow/', views.profile_follow,
         name='profile_follow'),
    path('<str:username>/unfollow/', views.profile_unfollow,
         name='profile_unfollow'),
    path('<str:username>/', views.profile, name='profile'),
    path('<str:username>/<int:post_id>/', views.post_view, name='post'),
    path('<str:username>/<int:post_id>/edit/',
         views.post_edit, name='post_edit'),
    path('<str:username>/<int:post_id>/delete/',
         views.post_delete, name='post_delete'),
    path('<str:username>/<int:post_id>/comment/',
         views.add_comment, name='add_comment'),
]
