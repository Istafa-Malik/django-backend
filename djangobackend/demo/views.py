import os
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import FolderAccess
from django.conf import settings
from .permissions import is_admin, can_view_folder, can_rename_folder, can_delete_folder
from .serializers import LoginSerializer
from rest_framework.permissions import IsAuthenticated
from .middleware import get_folders, get_files, download, rename, delete_file_folder, create_file, upload_fol, create_folder, login_user, logout_user, users, folders, folder_access

@api_view(['POST'])
def login(request):
    return login_user(request)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    return logout_user(request)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_folders(request):
    user = request.user
    folders = []
    db_entries = FolderAccess.objects.filter(user=user)
    db_has_folders = db_entries.exists()
    try:
        disk_folders = [
            name for name in os.listdir(settings.MEDIA_ROOT)
            if os.path.isdir(os.path.join(settings.MEDIA_ROOT, name)) and not name.startswith('.')
        ]
    except FileNotFoundError:
        disk_folders = []

    disk_has_folders = len(disk_folders) > 0
    if not db_has_folders and not disk_has_folders:
        return Response({"message": "No folders found."})
    if is_admin(user):
        try:
            top_level_folders = [
                f for f in os.listdir(settings.MEDIA_ROOT)
                if os.path.isdir(os.path.join(settings.MEDIA_ROOT, f)) and not f.startswith('.')
            ]
        except Exception:
            top_level_folders = []

        for folder in top_level_folders:
            abs_folder_path = os.path.join(settings.MEDIA_ROOT, folder)
            try:
                all_items = os.listdir(abs_folder_path)
                subfolders = [
                    sf for sf in all_items
                    if os.path.isdir(os.path.join(abs_folder_path, sf)) and not sf.startswith('.')
                ]
            except Exception:
                subfolders = []

            folders.append({
                "folder_path": folder,
                "can_view": True,
                "can_edit": True,
                "can_delete": True,
                "subfolders": subfolders
            })

    else:
        access_entries = FolderAccess.objects.filter(user=user)

        if not access_entries.exists():
            return Response({"error": "You do not have access to any folders."})

        for entry in access_entries:
            rel_folder_path = entry.folder_path

            if not can_view_folder(user, rel_folder_path):
                continue

            abs_folder_path = os.path.join(settings.MEDIA_ROOT, rel_folder_path)
            try:
                all_items = os.listdir(abs_folder_path)
                subfolders = [
                    f for f in all_items
                    if os.path.isdir(os.path.join(abs_folder_path, f)) and not f.startswith('.')
                ]
            except Exception:
                subfolders = []

            folders.append({
                "folder_path": rel_folder_path,
                "can_view": True,
                "can_edit": can_rename_folder(user, rel_folder_path),
                "can_delete": can_delete_folder(user, rel_folder_path),
                "subfolders": subfolders
            })
    return Response({"folders": folders})

    
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def file_access(request):
#     return get_file_access(request)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def list_files(request):
    return get_files(request)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def download_folder(request):
    return download(request)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit(request):
    return rename(request)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete(request):
    return delete_file_folder(request)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_folder(request):
    return upload_fol(request)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create(request):
    return create_file(request)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_fold(request):
    return create_folder(request)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_users(request):
    return users(request)        

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_folders(request):
    return folders(request)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_folder_access(request):
    return folder_access(request)