from django.urls import path
from .views import login_view, list_files, list_folders, download_folder,edit, delete, create, upload_folder
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/', login_view, name='login'),
    path('dashboard/', list_folders, name='folders'),
    path('dashboard/files', list_files, name='files'),
    path('download-folder/', download_folder, name='download-folder'),
    path('edit/', edit, name='edit'),
    path('delete/', delete, name='delete'),
    path('upload-file/', create, name='create'),
    path('upload-folder/', upload_folder, name='upload-folder')
]
