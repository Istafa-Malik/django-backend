import os
from django.conf import settings
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .permissions import is_admin
from .models import Folder, FolderAccess, User
import logging
from .middleware import (
    login_user, logout_user, get_files, download, rename, delete_file_folder,
    restore_trash, trash, get_trash, upload_fol, upload_file, create_folder,
    users, folders, folder_access, user_permissions as get_user_permissions, 
    delete_from_trash
)

logger = logging.getLogger(__name__)

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
    folders_list = []

    try:
        # Get all top-level folders from filesystem
        disk_folders = [
            name for name in os.listdir(settings.MEDIA_ROOT)
            if os.path.isdir(os.path.join(settings.MEDIA_ROOT, name)) and not name.startswith('.')
        ]
    except FileNotFoundError:
        disk_folders = []
    except Exception as e:
        disk_folders = []

    # Get all folder access records for the user (including trashed for filtering)
    folder_access_qs = FolderAccess.objects.filter(user=user, folder__isnull=False).select_related('folder')
    
    # Create maps for quick lookup
    all_folders_map = {fa.folder.folder_path: fa for fa in folder_access_qs}
    trashed_folders = {fa.folder.folder_path for fa in folder_access_qs if fa.is_trashed or (fa.folder and fa.folder.is_trashed)}

    # If user is admin, show all NON-TRASHED folders
    if is_admin(user):
        for folder_name in disk_folders:
            # Skip if folder is trashed
            if folder_name in trashed_folders:
                continue
                
            abs_folder_path = os.path.join(settings.MEDIA_ROOT, folder_name)
            
            try:
                # Get subfolders
                all_items = os.listdir(abs_folder_path)
                subfolders = [
                    sf for sf in all_items
                    if os.path.isdir(os.path.join(abs_folder_path, sf)) and not sf.startswith('.')
                ]
            except Exception:
                subfolders = []

            # Get or create folder access record
            access = all_folders_map.get(folder_name)
            if not access:
                # Create access record if it doesn't exist
                folder_obj, created = Folder.objects.get_or_create(
                    folder_path=folder_name,
                    defaults={'name': folder_name, 'owner': user, 'is_trashed': False}
                )
                access, created = FolderAccess.objects.get_or_create(
                    folder=folder_obj,
                    user=user,
                    defaults={
                        'can_view': True,
                        'can_edit': True,
                        'can_delete': True,
                        'can_download': True,
                        'is_trashed': False
                    }
                )
                all_folders_map[folder_name] = access

            # Double-check it's not trashed
            if access.is_trashed or (access.folder and access.folder.is_trashed):
                continue

            folders_list.append({
                "owner": access.folder.owner.username if access.folder else user.username,
                "folder_path": folder_name,
                "name": access.folder.name if access.folder else folder_name,
                "can_view": True,
                "can_edit": True,
                "can_delete": True,
                "can_download": True,
                "is_trashed": access.is_trashed,
                "trashed_at": access.trashed_at,
                "last_modified": access.last_modified,
                "subfolders": subfolders
            })

    # If user is not admin, show only accessible NON-TRASHED folders
    else:
        for folder_name in disk_folders:
            # Skip if folder is trashed
            if folder_name in trashed_folders:
                continue
                
            access = all_folders_map.get(folder_name)
            
            # Skip if no access, no view permission, or trashed
            if not access or not access.can_view or access.is_trashed:
                continue

            # Double-check folder is not trashed
            if access.folder and access.folder.is_trashed:
                continue
                
            abs_folder_path = os.path.join(settings.MEDIA_ROOT, folder_name)
            try:
                all_items = os.listdir(abs_folder_path)
                subfolders = [
                    f for f in all_items
                    if os.path.isdir(os.path.join(abs_folder_path, f)) and not f.startswith('.')
                ]
            except Exception:
                subfolders = []

            folders_list.append({
                "owner": access.folder.owner.username if access.folder else 'Unknown',
                "folder_path": folder_name,
                "name": access.folder.name if access.folder else folder_name,
                "can_view": access.can_view,
                "can_edit": access.can_edit,
                "can_delete": access.can_delete,
                "can_download": access.can_download,
                "is_trashed": access.is_trashed,
                "trashed_at": access.trashed_at,
                "last_modified": access.last_modified,
                "subfolders": subfolders
            })

    return Response({"folders": folders_list})

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
def restore_from_trash(request):
    return restore_trash(request)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def move_to_trash(request):
    return trash(request)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_from_trash(request):
    return get_trash(request)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_folder(request):
    return upload_fol(request)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create(request):
    return upload_file(request)

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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_permissions(request):
    return get_user_permissions(request)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_from_trash_view(request):
    return delete_from_trash(request)