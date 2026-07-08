from django.urls import path

from notifications import views


app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='list'),
    path('unread/', views.unread_json, name='unread_json'),
    path('<int:pk>/read/', views.mark_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
]
