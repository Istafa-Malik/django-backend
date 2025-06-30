from django.urls import path
from .views import login_view, user_files_view

urlpatterns = [
    path('login/', login_view, name='login'),
    path('dashboard/', user_files_view, name='user-files')
]
