import os
import io
import zipfile
import shutil
from django.conf import settings
from django.http import FileResponse
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from . import errors
from .permissions import is_admin
from .models import Folder, FolderAccess, FileAccess, UserPermissions, User
from .serializers import FolderAccessSerializer, FileAccessSerializer, LoginSerializer

def login_user(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        print('validated data is: ', serializer.validated_data)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        user_data = {
            "username": user.username,
            "role": user.role 
        }
        return Response({
            "message": "Login successful",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user_data": user_data
        })
    return Response(serializer.errors, status=400)

def logout_user(request):
    try:
        refresh_token = request.data.get("refresh")
        if refresh_token is None:
            return Response({errors.Error: "Refresh token is required"}, status=400)
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"detail": "Logout successful"})
    except Exception as e:
        return Response({errors.Error: str(e)}, status=400)

def get_files(request):
    user = request.user
    rel_folder_path = request.data.get("folder_path", "").strip()
    abs_folder_path = os.path.join(settings.MEDIA_ROOT, rel_folder_path)

    if not rel_folder_path or not os.path.isdir(abs_folder_path):
        return Response({errors.Error: errors.INVALID_FOLDER_PATH}, status=400)

    # === List Files ===
    all_files = [
        f for f in os.listdir(abs_folder_path)
        if os.path.isfile(os.path.join(abs_folder_path, f))
    ]
    file_paths = [os.path.join(rel_folder_path, f) for f in all_files]
    accessible_files = []
    
    # Only get NON-TRASHED files
    file_access_qs = FileAccess.objects.filter(file_path__in=file_paths, is_trashed=False)
    file_access_map = {f.file_path: f for f in file_access_qs}

    if is_admin(user):
        for file_name in all_files:
            rel_file_path = os.path.join(rel_folder_path, file_name)
            db_entry = file_access_map.get(rel_file_path)
            if db_entry and not db_entry.is_trashed:  # Only non-trashed
                file_url = f"{settings.MEDIA_URL}{rel_file_path}"
                download_url = request.build_absolute_uri(f"/media/{rel_file_path}")
                accessible_files.append({
                    "owner": db_entry.user.username,
                    "file_name": file_name,
                    "file_path": rel_file_path,
                    "file_url": file_url,
                    "download_url": download_url,
                    "can_view": True,
                    "can_edit": True,
                    "can_delete": True,
                    "can_download": True,
                    "is_trashed": db_entry.is_trashed,
                    "trashed_at": db_entry.trashed_at,
                    "last_modified": db_entry.last_modified
                })
    else:
        access_records = file_access_qs.filter(user=user, can_view=True, is_trashed=False)
        access_map = {record.file_path: record for record in access_records}
        for file_name in all_files:
            rel_file_path = os.path.join(rel_folder_path, file_name)
            access = access_map.get(rel_file_path)
            if access and not access.is_trashed:  # Only non-trashed
                file_url = f"{settings.MEDIA_URL}{rel_file_path}"
                download_url = request.build_absolute_uri(f"/media/{rel_file_path}")
                accessible_files.append({
                    "owner": access.user.username,
                    "file_name": file_name,
                    "file_path": rel_file_path,
                    "file_url": file_url,
                    "download_url": download_url,
                    "can_view": access.can_view,
                    "can_edit": access.can_edit,
                    "can_delete": access.can_delete,
                    "can_download": access.can_download,
                    "is_trashed": access.is_trashed,
                    "trashed_at": access.trashed_at,
                    "last_modified": access.last_modified
                })

    # === List Folders === (Only NON-TRASHED)
    all_folders = [
        d for d in os.listdir(abs_folder_path)
        if os.path.isdir(os.path.join(abs_folder_path, d))
    ]
    full_folder_paths = [os.path.join(rel_folder_path, d) for d in all_folders]
    accessible_folders = []
    
    # Only get NON-TRASHED folders
    folder_qs = Folder.objects.filter(folder_path__in=full_folder_paths, is_trashed=False)
    folder_owner_map = {f.folder_path: f.owner.username for f in folder_qs}
    folder_access_qs = FolderAccess.objects.filter(
        folder__folder_path__in=full_folder_paths, 
        is_trashed=False
    ).select_related('folder')
    folder_access_map = {f.folder.folder_path: f for f in folder_access_qs if not f.folder.is_trashed}

    if is_admin(user):
        for folder_name in all_folders:
            folder_rel_path = os.path.join(rel_folder_path, folder_name)
            db_entry = folder_access_map.get(folder_rel_path)
            if db_entry and not db_entry.is_trashed and (not db_entry.folder or not db_entry.folder.is_trashed):
                accessible_folders.append({
                    "owner": folder_owner_map.get(folder_rel_path, 'Unknown'),
                    "name": folder_name,
                    "path": folder_rel_path,
                    "can_view": True,
                    "can_edit": True,
                    "can_delete": True,
                    "can_download": True,
                    "is_trashed": db_entry.is_trashed,
                    "trashed_at": db_entry.trashed_at,
                    "last_modified": db_entry.last_modified
                })
    else:
        folder_access_records = folder_access_qs.filter(user=user, can_view=True, is_trashed=False)
        folder_access_map = {f.folder.folder_path: f for f in folder_access_records if not f.folder.is_trashed}
        for folder_name in all_folders:
            folder_rel_path = os.path.join(rel_folder_path, folder_name)
            access = folder_access_map.get(folder_rel_path)
            if access and not access.is_trashed and (not access.folder or not access.folder.is_trashed):
                accessible_folders.append({
                    "owner": folder_owner_map.get(folder_rel_path, 'Unknown'),
                    "name": folder_name,
                    "path": folder_rel_path,
                    "can_view": access.can_view,
                    "can_edit": access.can_edit,
                    "can_delete": access.can_delete,
                    "can_download": access.can_download,
                    "is_trashed": access.is_trashed,
                    "trashed_at": access.trashed_at,
                    "last_modified": access.last_modified
                })

    return Response({
        "folder_path": rel_folder_path,
        "files": accessible_files,
        "folders": accessible_folders
    })

def download(request):
    folder_path = request.data.get("folder_path")
    if not folder_path:
        return Response({errors.Error: errors.PATH_NOT_PROVIDED}, status=400)

    abs_folder_path = os.path.join(settings.MEDIA_ROOT, folder_path)
    if not FolderAccess.objects.filter(folder__folder_path=folder_path, user=request.user).exists():
        return Response({errors.Error: errors.FOLDER_DOES_NOT_EXISTS}, status=404)
    
    access = FolderAccess.objects.filter(folder__folder_path=folder_path, user=request.user).first()
    if not access or not access.can_download:
        return Response({errors.Error: errors.DOWNLOAD_PERMISSION}, status=403)

    zip_stream = io.BytesIO()
    with zipfile.ZipFile(zip_stream, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(abs_folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, abs_folder_path)
                zipf.write(file_path, arcname)

    zip_stream.seek(0)
    folder_name = os.path.basename(abs_folder_path)
    response = FileResponse(zip_stream, as_attachment=True, filename=f"{folder_name}.zip")
    return response

def rename(request):
    old_path = request.data.get('old_path')
    new_name = request.data.get('new_name')

    if not old_path:
        return Response({errors.Error: errors.MISSING__OLDPATH}, status=400)
    elif not new_name:
        return Response({errors.Error: errors.MISSING_NEWNAME}, status=400)

    # Normalize the path (remove /media/ prefix and handle backslashes)
    relative_path = old_path.replace('/media/', '')
    relative_path = relative_path.replace('\\', '/')
    
    abs_old_path = os.path.join(settings.MEDIA_ROOT, relative_path)
    dir_name = os.path.dirname(abs_old_path)
    abs_new_path = os.path.join(dir_name, new_name)

    if not os.path.exists(abs_old_path):
        return Response({errors.Error: f"Item does not exist at: {abs_old_path}"}, status=404)

    try:
        # Rename in filesystem
        os.rename(abs_old_path, abs_new_path)
        
        # Calculate new relative path
        old_dir = os.path.dirname(relative_path)
        rel_new_path = os.path.join(old_dir, new_name) if old_dir else new_name
        rel_new_path = rel_new_path.replace('\\', '/')

        if os.path.isdir(abs_new_path):
            # Update Folder model (not FolderAccess)
            Folder.objects.filter(folder_path=relative_path).update(
                folder_path=rel_new_path,
                name=new_name
            )
            # FolderAccess will automatically reflect the change through the foreign key
        else:
            # Update FileAccess for files
            FileAccess.objects.filter(file_path=relative_path).update(file_path=rel_new_path)

        return Response({"message": "Renamed successfully", "new_path": rel_new_path})
    except Exception as e:
        return Response({errors.Error: str(e)}, status=400)

def delete_file_folder(request):
    # Check if data is nested in 'payload'
    if 'payload' in request.data:
        path = request.data.get('payload', {}).get('path')
    else:
        path = request.data.get('path')
    
    print(f"DELETE - Request data: {request.data}")
    print(f"DELETE - Path received: {path}")
    
    if not path:
        return Response({errors.Error: errors.PATH_NOT_PROVIDED}, status=400)

    # Clean the path
    clean_path = path.replace('/media/', '').replace('\\', '/')
    if clean_path.startswith('./'):
        clean_path = clean_path[2:]
    
    print(f"DELETE - Cleaned path: {clean_path}")

    # Try to find in database first - try exact match first
    folder = Folder.objects.filter(folder_path=clean_path).first()
    
    # If not found, try to find by basename (for nested folders)
    if not folder:
        # Extract just the folder name from the path
        folder_name = os.path.basename(clean_path)
        folder = Folder.objects.filter(folder_path__endswith=folder_name).first()
        print(f"DELETE - Found by basename '{folder_name}': {folder}")
    
    file_access = None
    
    if folder:
        # It's a folder
        abs_path = os.path.join(settings.MEDIA_ROOT, folder.folder_path)
        print(f"DELETE - Folder absolute path: {abs_path}")
        
        # Check permissions
        if not (is_admin(request.user) or folder.owner == request.user):
            user_access = FolderAccess.objects.filter(folder=folder, user=request.user).first()
            if not user_access or not user_access.can_delete:
                return Response({errors.Error: "Permission denied to delete folder"}, status=403)
    else:
        # It's probably a file
        file_access = FileAccess.objects.filter(file_path=clean_path).first()
        if not file_access:
            # Try to find file by basename
            file_name = os.path.basename(clean_path)
            file_access = FileAccess.objects.filter(file_path__endswith=file_name).first()
            print(f"DELETE - Found file by basename '{file_name}': {file_access}")
            
        if file_access:
            abs_path = os.path.join(settings.MEDIA_ROOT, file_access.file_path)
            print(f"DELETE - File absolute path: {abs_path}")
            
            # Check permissions
            if not is_admin(request.user):
                user_file_access = FileAccess.objects.filter(file_path=file_access.file_path, user=request.user).first()
                if not user_file_access or not user_file_access.can_delete:
                    return Response({errors.Error: "Permission denied to delete file"}, status=403)
        else:
            print(f"DELETE - Item not found in database: {clean_path}")
            return Response({errors.Error: errors.PATH_DOES_NOT_EXIST}, status=404)

    if not os.path.exists(abs_path):
        print(f"DELETE - Path does not exist in filesystem: {abs_path}")
        return Response({errors.Error: errors.PATH_DOES_NOT_EXIST}, status=404)

    try:
        if folder:
            # Delete folder
            print(f"DELETE - Deleting folder: {abs_path}")
            shutil.rmtree(abs_path)
            FolderAccess.objects.filter(folder=folder).delete()
            folder.delete()
            print(f"Successfully deleted folder: {folder.folder_path}")
        else:
            # Delete file
            print(f"DELETE - Deleting file: {abs_path}")
            os.remove(abs_path)
            FileAccess.objects.filter(file_path=file_access.file_path).delete()
            print(f"Successfully deleted file: {file_access.file_path}")
            
        return Response({errors.Success: errors.DELETED_SUCCESSFULLY})
    except Exception as e:
        print(f"Error during deletion: {e}")
        return Response({errors.Error: str(e)}, status=400)
def restore_trash(request):
    user = request.user
    if not is_admin(user):
        return Response({errors.Error: errors.UNAUTHORIZED}, status=403)
    
    item_type = request.data.get("type")
    path = request.data.get("path")

    print(f"RESTORE TRASH - Type: {item_type}, Path: {path}")

    if not item_type:
        return Response({errors.Error: "Type not provided"}, status=400)
    if not path:
        return Response({errors.Error: "Path not provided"}, status=400)

    # Clean the path
    clean_path = path.replace('\\', '/')
    if clean_path.startswith('./'):
        clean_path = clean_path[2:]

    if item_type == 'folder':
        # Find folder by path
        folder = Folder.objects.filter(folder_path=clean_path, is_trashed=True).first()
        if not folder:
            # Try by basename
            folder_name = os.path.basename(clean_path)
            folder = Folder.objects.filter(folder_path__endswith=folder_name, is_trashed=True).first()
        
        if folder:
            # Update Folder model
            Folder.objects.filter(folder_path=folder.folder_path).update(is_trashed=False, trashed_at=None)
            # Update FolderAccess
            FolderAccess.objects.filter(folder=folder).update(is_trashed=False, trashed_at=None)
            return Response({"success": True, "message": "Folder restored successfully"})
        else:
            return Response({errors.Error: "Folder not found or not trashed"}, status=404)

    elif item_type == 'file':
        # Find file by path
        file_access = FileAccess.objects.filter(file_path=clean_path, is_trashed=True).first()
        if not file_access:
            # Try by basename
            file_name = os.path.basename(clean_path)
            file_access = FileAccess.objects.filter(file_path__endswith=file_name, is_trashed=True).first()
        
        if file_access:
            file_access.is_trashed = False
            file_access.trashed_at = None
            file_access.save()
            return Response({"success": True, "message": "File restored successfully"})
        else:
            return Response({errors.Error: "File not found or not trashed"}, status=404)

    else:
        return Response({errors.Error: errors.INVALID_TYPE}, status=400)

def trash(request):
    try:
        # Check if data is nested in 'payload'
        if 'payload' in request.data:
            path = request.data.get('payload', {}).get("path")
            item_type = request.data.get('payload', {}).get("type")
        else:
            path = request.data.get("path")
            item_type = request.data.get("type")

        print(f"TRASH - Request data: {request.data}")
        print(f"TRASH - Path: {path}, Type: {item_type}")

        # Clean and normalize the path
        if path and path.startswith("/media/"):
            path = path[len("/media/"):]
        
        clean_path = path.replace('\\', '/') if path else ""
        if clean_path.startswith('./'):
            clean_path = clean_path[2:]

        now = timezone.now()
        updated = []

        if item_type == "file":
            # Try to find file with exact path first
            file_access = FileAccess.objects.filter(file_path=clean_path).first()
            if not file_access:
                # Try to find by basename
                file_name = os.path.basename(clean_path)
                file_access = FileAccess.objects.filter(file_path__endswith=file_name).first()
            
            if file_access:
                file_access.is_trashed = True
                file_access.trashed_at = now
                file_access.save()
                updated.append(file_access.file_path)
                print(f"Trashed file: {file_access.file_path}")
            else:
                return Response({errors.Error: errors.FILE_NOT_FOUND}, status=404)

        elif item_type == "folder":
            # Try to find folder with exact path first
            folder = Folder.objects.filter(folder_path=clean_path).first()
            if not folder:
                # Try to find by basename
                folder_name = os.path.basename(clean_path)
                folder = Folder.objects.filter(folder_path__endswith=folder_name).first()
            
            if folder:
                # Update Folder model
                Folder.objects.filter(folder_path=folder.folder_path).update(
                    is_trashed=True, 
                    trashed_at=now
                )
                # Update FolderAccess
                FolderAccess.objects.filter(folder=folder).update(
                    is_trashed=True, 
                    trashed_at=now
                )
                updated.append(folder.folder_path)
                print(f"Trashed folder: {folder.folder_path}")
            else:
                return Response({errors.Error: errors.FOLDER_NOT_FOUND}, status=404)

        else:
            return Response({errors.Error: errors.INVALID_TYPE}, status=400)

        return Response({
            errors.Success: True,
            "updated": updated
        })
    except Exception as e:
        print(f"Error in trash function: {e}")
        return Response({errors.Error: str(e)}, status=400)
def get_trash(request):
    user = request.user
    if is_admin(user):
        # Get trashed folders with their access records
        folders = Folder.objects.filter(is_trashed=True)
        folder_data = []
        for folder in folders:
            access = FolderAccess.objects.filter(folder=folder, is_trashed=True).first()
            folder_data.append({
                "id": folder.id,
                "folder_path": folder.folder_path,
                "name": folder.name,
                "owner": folder.owner.username,
                "trashed_at": access.trashed_at if access else folder.trashed_at,
                "type": "folder"
            })
        
        # Get trashed files
        files = FileAccess.objects.filter(is_trashed=True)
        file_data = []
        for file in files:
            file_data.append({
                "id": file.id,
                "file_path": file.file_path,
                "file_name": os.path.basename(file.file_path),
                "owner": file.user.username,
                "trashed_at": file.trashed_at,
                "type": "file"
            })
        
        return Response({
            "success": True,
            "folders": folder_data,
            "files": file_data
        })
    else:
        return Response({errors.Error: errors.UNAUTHORIZED}, status=403)

def create_folder(request):
    name = request.data.get('name')
    path = request.data.get('path') or '.'
    
    # Clean and normalize the path
    if path == '.':
        clean_path = name
    else:
        clean_path = os.path.join(path, name)
    
    # Normalize path to use forward slashes (Unix style)
    clean_path = clean_path.replace('\\', '/')
    
    # Remove any leading ./ if present
    if clean_path.startswith('./'):
        clean_path = clean_path[2:]
    
    abs_parent_path = os.path.join(settings.MEDIA_ROOT, path)
    abs_new_path = os.path.join(abs_parent_path, name)

    # Check if folder already exists in database OR filesystem
    # Normalize database paths for comparison
    existing_db_paths = Folder.objects.values_list('folder_path', flat=True)
    normalized_db_paths = [p.replace('\\', '/') for p in existing_db_paths]
    
    if clean_path in normalized_db_paths or os.path.exists(abs_new_path):
        return Response({errors.Error: errors.FOLDER_ALREADY_EXISTS}, status=400)

    try:
        # Create folder in filesystem
        os.makedirs(abs_new_path, exist_ok=True)
        
        # Create folder in database with normalized path
        folder = Folder.objects.create(
            folder_path=clean_path,
            name=name,
            owner=request.user,
            is_trashed=False
        )
        
        # Create folder access for the owner
        FolderAccess.objects.create(
            folder=folder,
            user=request.user,
            can_view=True,
            can_edit=True,
            can_delete=True,
            can_download=True,
            is_trashed=False
        )
        
        return Response({errors.Success: errors.FOLDER_CREATED_SUCCESSFULLY})
    except Exception as e:
        # Clean up if creation fails
        if os.path.exists(abs_new_path):
            shutil.rmtree(abs_new_path)
        return Response({errors.Error: str(e)}, status=400)

def upload_file(request):
    uploaded_file = request.FILES.get('file')
    upload_path = request.POST.get('path') or ''

    if not uploaded_file:
        return Response({errors.Error: errors.MISSING_FILE}, status=400)

    if upload_path.strip() == '':
        dest_dir = settings.MEDIA_ROOT
        db_path = uploaded_file.name
    else:
        dest_dir = os.path.join(settings.MEDIA_ROOT, upload_path)
        db_path = os.path.join(upload_path, uploaded_file.name)

    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, uploaded_file.name)
    with open(dest_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    FileAccess.objects.create(
        file_path=db_path,
        user=request.user,
        can_view=True,
        can_edit=True,
        can_delete=True,
        can_download=True,
        is_trashed=False
    )
    return Response({errors.Success: errors.FILE_UPLOADED_SUCCESSFULLY})

def upload_fol(request):
    uploaded_files = request.FILES.getlist('files')
    relative_paths = request.POST.getlist('paths')
    base_path = request.POST.get('base_path', '').strip()
    folder_paths_set = set()

    for i, file in enumerate(uploaded_files):
        rel_path = relative_paths[i] if i < len(relative_paths) else file.name
        full_path = os.path.join(base_path, rel_path)
        abs_path = os.path.join(settings.MEDIA_ROOT, full_path)

        parent_folder_path = os.path.dirname(full_path)
        while parent_folder_path and parent_folder_path not in folder_paths_set:
            abs_folder = os.path.join(settings.MEDIA_ROOT, parent_folder_path)
            os.makedirs(abs_folder, exist_ok=True)
            folder_paths_set.add(parent_folder_path)

            folder, created = Folder.objects.get_or_create(
                folder_path=parent_folder_path,
                defaults={
                    'name': os.path.basename(parent_folder_path),
                    'owner': request.user,
                    'is_trashed': False
                }
            )
            FolderAccess.objects.get_or_create(
                folder=folder,
                user=request.user,
                defaults={
                    'can_view': True,
                    'can_edit': True,
                    'can_delete': True,
                    'can_download': True,
                    'is_trashed': False
                }
            )
            parent_folder_path = os.path.dirname(parent_folder_path)

        with open(abs_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        FileAccess.objects.create(
            file_path=full_path,
            user=request.user,
            can_view=True,
            can_edit=True,
            can_delete=True,
            can_download=True,
            is_trashed=False
        )

    return Response({
        errors.Success: errors.FOLDER_UPLOADED_SUCCESSFULLY
    })

def users(request):
    if request.user.role.lower() == 'admin':
        users_data = []
        all_users = User.objects.all()

        for user in all_users:
            try:
                user_perm = UserPermissions.objects.get(user=user)
                can_upload_folder = user_perm.can_upload_folder
                can_upload_file = user_perm.can_upload_file
            except UserPermissions.DoesNotExist:
                can_upload_folder = False
                can_upload_file = False

            folder_perms = FolderAccess.objects.filter(user=user).values(
                'folder__folder_path', 'can_view', 'can_edit', 'can_delete', 'can_download'
            )
            file_perms = FileAccess.objects.filter(user=user).values(
                'file_path', 'can_view', 'can_edit', 'can_delete', 'can_download'
            )

            users_data.append({
                "username": user.username,
                "role": user.role,
                "can_upload_folder": can_upload_folder,
                "can_upload_file": can_upload_file,
                "folder_permissions": list(folder_perms),
                "file_permissions": list(file_perms)
            })

        return Response({"users": users_data})
    else:
        return Response({errors.Error: errors.USER_IS_NOT_ADMIN}, status=403)

def folders(request):
    folders = Folder.objects.values_list('folder_path', flat=True).distinct()
    top_level_folders = [path for path in folders if '/' not in path and '\\' not in path]
    return Response({
        "folders": [{"folder_path": path} for path in top_level_folders]
    })

def folder_access(request):
    if request.user.role.lower() != 'admin':
        return Response({errors.Error: errors.USER_IS_NOT_ADMIN}, status=403)

    for item in request.data:
        usernames = item.get("username", [])
        folder_paths = item.get("folder_path", [])
        can_upload_folder = item.get("can_upload_folder")
        can_upload_file = item.get("can_upload_file")
        can_view = item.get("can_view")
        can_edit = item.get("can_edit")
        can_delete = item.get("can_delete")
        can_download = item.get("can_download")

        if isinstance(usernames, str):
            usernames = [usernames]
        if isinstance(folder_paths, str):
            folder_paths = [folder_paths]

        if not User.objects.filter(username__in=usernames).exists():
            return Response({errors.Error: errors.SELECTED_USER_DOES_NOT_EXIST}, status=400)
        if not folder_paths and (can_view or can_edit or can_delete or can_download):
            return Response({errors.Error: errors.PATH_NOT_PROVIDED}, status=400)

        updated_objs = []

        for username in usernames:
            user = User.objects.get(username=username)
            if user.role.lower() == 'admin':
                can_upload_folder = True
                can_upload_file = True
                can_view = True
                can_edit = True
                can_delete = True
                can_download = True

            UserPermissions.objects.update_or_create(
                user=user,
                defaults={
                    'can_upload_folder': can_upload_folder,
                    'can_upload_file': can_upload_file
                }
            )

            for folder_path in folder_paths:
                folder = Folder.objects.filter(folder_path=folder_path).first()
                if not folder:
                    return Response({errors.Error: f"Folder {folder_path} does not exist"}, status=404)

                if user != request.user:
                    obj, created = FolderAccess.objects.update_or_create(
                        user=user,
                        folder=folder,
                        defaults={
                            'can_view': can_view,
                            'can_edit': can_edit,
                            'can_delete': can_delete,
                            'can_download': can_download,
                        }
                    )
                    updated_objs.append(obj)

                FolderAccess.objects.update_or_create(
                    user=request.user,
                    folder=folder,
                    defaults={
                        'can_view': True,
                        'can_edit': True,
                        'can_delete': True,
                        'can_download': True,
                    }
                )

                full_folder_path = os.path.join(settings.MEDIA_ROOT, folder_path)
                if os.path.exists(full_folder_path):
                    for item in os.listdir(full_folder_path):
                        if not item.startswith('.'):
                            item_path = os.path.join(folder_path, item)
                            FileAccess.objects.update_or_create(
                                user=user,
                                file_path=item_path,
                                defaults={
                                    "can_view": can_view,
                                    "can_edit": can_edit,
                                    "can_delete": can_delete,
                                    "can_download": can_download,
                                }
                            )

        if updated_objs:
            FolderAccess.objects.bulk_update(updated_objs, ['can_view', 'can_edit', 'can_delete', 'can_download'])

    return Response({"message": f"Permissions assigned to {len(updated_objs)} folder records, and their files."})

def user_permissions(request):
    user = request.user
    try:
        user_perm = UserPermissions.objects.get(user=user)
        return Response({
            "username": user.username,
            "can_upload_folder": user_perm.can_upload_folder,
            "can_upload_file": user_perm.can_upload_file
        })
    except UserPermissions.DoesNotExist:
        return Response({
            "username": user.username,
            "can_upload_folder": False,
            "can_upload_file": False
        })

def delete_from_trash(request):
    try:
        # Check if data is nested in 'payload'
        if 'payload' in request.data:
            item_type = request.data.get('payload', {}).get("type")
            path = request.data.get('payload', {}).get("path")
        else:
            item_type = request.data.get("type")
            path = request.data.get("path")
        
        print(f"DELETE FROM TRASH - Request data: {request.data}")
        print(f"DELETE FROM TRASH - Type: {item_type}, Path: {path}")

        if not item_type:
            return Response({errors.Error: "Type not provided"}, status=400)
        if not path:
            return Response({errors.Error: "Path not provided"}, status=400)

        # Clean the path
        clean_path = path.replace('\\', '/')
        if clean_path.startswith('./'):
            clean_path = clean_path[2:]
        
        print(f"DELETE FROM TRASH - Cleaned path: {clean_path}")

        if item_type == "folder":
            # Find folder in trash
            folder = Folder.objects.filter(folder_path=clean_path, is_trashed=True).first()
            if not folder:
                # Try by basename
                folder_name = os.path.basename(clean_path)
                folder = Folder.objects.filter(folder_path__endswith=folder_name, is_trashed=True).first()
                print(f"DELETE FROM TRASH - Found folder by basename: {folder}")
            
            if folder:
                abs_path = os.path.join(settings.MEDIA_ROOT, folder.folder_path)
                print(f"DELETE FROM TRASH - Folder absolute path: {abs_path}")
                
                # Delete from filesystem
                if os.path.exists(abs_path):
                    shutil.rmtree(abs_path)
                    print(f"DELETE FROM TRASH - Deleted folder from filesystem: {abs_path}")
                
                # Delete from database
                FolderAccess.objects.filter(folder=folder).delete()
                folder.delete()
                print(f"DELETE FROM TRASH - Deleted folder from database: {folder.folder_path}")
                
                return Response({"success": True, "message": "Folder permanently deleted from trash"})
            else:
                return Response({errors.Error: "Folder not found in trash"}, status=404)

        elif item_type == "file":
            # Find file in trash
            file_access = FileAccess.objects.filter(file_path=clean_path, is_trashed=True).first()
            if not file_access:
                # Try by basename
                file_name = os.path.basename(clean_path)
                file_access = FileAccess.objects.filter(file_path__endswith=file_name, is_trashed=True).first()
                print(f"DELETE FROM TRASH - Found file by basename: {file_access}")
            
            if file_access:
                abs_path = os.path.join(settings.MEDIA_ROOT, file_access.file_path)
                print(f"DELETE FROM TRASH - File absolute path: {abs_path}")
                
                # Delete from filesystem
                if os.path.exists(abs_path):
                    os.remove(abs_path)
                    print(f"DELETE FROM TRASH - Deleted file from filesystem: {abs_path}")
                
                # Delete from database
                file_access.delete()
                print(f"DELETE FROM TRASH - Deleted file from database: {file_access.file_path}")
                
                return Response({"success": True, "message": "File permanently deleted from trash"})
            else:
                return Response({errors.Error: "File not found in trash"}, status=404)

        else:
            return Response({errors.Error: errors.INVALID_TYPE}, status=400)
            
    except Exception as e:
        print(f"DELETE FROM TRASH - Error: {e}")
        return Response({errors.Error: str(e)}, status=400)