from django.urls import path
from .views import login_view, list_files, list_folders, download_folder
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/', login_view, name='login'),
    path('dashboard/', list_folders, name='folders'),
    path('dashboard/files', list_files, name='files'),
    path('download-folder/', download_folder, name='download-folder')
]
