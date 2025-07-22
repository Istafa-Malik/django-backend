import os
from rest_framework.response import Response
from .models import FolderAccess, FileAccess, User, UserPermissions
from django.conf import settings
from django.http import FileResponse, HttpResponseBadRequest, Http404
import zipfile
import io
from demo import errors
import shutil
from .serializers import LoginSerializer, BulkFolderAccessSerializer, FileAccessSerializer, FolderAccessSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .permissions import is_admin, can_delete_folder, can_rename_folder, can_view_folder, check_permission
from django.utils import timezone
import json


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
    return Response(serializer.errors)

def logout_user(request):
    try:
        refresh_token = request.data.get("refresh")
        if refresh_token is None:
            return Response({errors.Error: "Refresh token is required"})
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"detail": "Logout successful"})
    except Exception as e:
        return Response({errors.Error: str(e)})

# def get_folders(request):
#     print('inside get folder')
#     user = request.user
#     folders = []
#     db_entries = FolderAccess.objects.filter(user=user)
#     db_has_folders = db_entries.exists()
#     print('db folders: ', db_has_folders)
#     # Check folders on disk (excluding hidden)
#     try:
#         disk_folders = [
#             name for name in os.listdir(settings.MEDIA_ROOT)
#             if os.path.isdir(os.path.join(settings.MEDIA_ROOT, name)) and not name.startswith('.')
#         ]
#     except FileNotFoundError:
#         disk_folders = []

#     disk_has_folders = len(disk_folders) > 0
#     print('disk has folders: ', disk_has_folders)
#     if not db_has_folders and not disk_has_folders:
#         return Response({"message": "No folders found."})
#     if is_admin(user):
#         try:
#             top_level_folders = [
#                 f for f in os.listdir(settings.MEDIA_ROOT)
#                 if os.path.isdir(os.path.join(settings.MEDIA_ROOT, f)) and not f.startswith('.')
#             ]
#         except Exception:
#             top_level_folders = []

#         for folder in top_level_folders:
#             abs_folder_path = os.path.join(settings.MEDIA_ROOT, folder)
#             try:
#                 all_items = os.listdir(abs_folder_path)
#                 subfolders = [
#                     sf for sf in all_items
#                     if os.path.isdir(os.path.join(abs_folder_path, sf)) and not sf.startswith('.')
#                 ]
#             except Exception:
#                 subfolders = []

#             folders.append({
#                 "folder_path": folder,
#                 "can_view": True,
#                 "can_edit": True,
#                 "can_delete": True,
#                 "subfolders": subfolders
#             })

#     else:
#         access_entries = FolderAccess.objects.filter(user=user)

#         if not access_entries.exists():
#             return Response({"error": "You do not have access to any folders."})

#         for entry in access_entries:
#             rel_folder_path = entry.folder_path

#             if not can_view_folder(user, rel_folder_path):
#                 continue  # Just to double-check access

#             abs_folder_path = os.path.join(settings.MEDIA_ROOT, rel_folder_path)
#             try:
#                 all_items = os.listdir(abs_folder_path)
#                 subfolders = [
#                     f for f in all_items
#                     if os.path.isdir(os.path.join(abs_folder_path, f)) and not f.startswith('.')
#                 ]
#             except Exception:
#                 subfolders = []

#             folders.append({
#                 "folder_path": rel_folder_path,
#                 "can_view": True,
#                 "can_edit": can_rename_folder(user, rel_folder_path),
#                 "can_delete": can_delete_folder(user, rel_folder_path),
#                 "subfolders": subfolders
#             })
#     return Response({"folders": folders})


                                            #Following function can be used as a specific access/permission function for a better code structure
                                            #for now I have commented it.


# def get_file_access(request):
#     user = request.user
#     rel_file_path = request.data.get("file_path", "").strip()
#     abs_file_path = os.path.join(settings.MEDIA_ROOT, rel_file_path)

#     if not os.path.isfile(abs_file_path):
#         return Response({"error": f"{rel_file_path} is not a valid file."}, status=400)

#     try:
#         access = FileAccess.objects.get(user=user, file_path=rel_file_path, can_view=True)
#     except FileAccess.DoesNotExist:
#         return Response({"error": "You do not have permission to view this file."}, status=403)

#     return Response({
#         "file_path": rel_file_path,
#         "can_view": access.can_view,
#         "can_edit": access.can_edit,
#         "can_delete": access.can_delete,
#         "file_url": f"/{rel_file_path}"
#     })



# def get_files(request):
#     user = request.user
#     rel_folder_path = request.data.get("folder_path", "").strip()
#     abs_folder_path = os.path.join(settings.MEDIA_ROOT, rel_folder_path)

#     if not rel_folder_path or not os.path.isdir(abs_folder_path):
#         return Response({"error": "Invalid folder path."})

#     # === List Files ===
#     all_files = [
#         f for f in os.listdir(abs_folder_path)
#         if os.path.isfile(os.path.join(abs_folder_path, f))
#     ]
#     file_paths = [os.path.join(rel_folder_path, f) for f in all_files]
#     access_records = FileAccess.objects.filter(user=user, file_path__in=file_paths)
#     access_map = {record.file_path: record for record in access_records}

#     accessible_files = []
#     if is_admin(user):
#          for file_name in all_files:
#             rel_file_path = os.path.join(rel_folder_path, file_name)
#             file_url = f"{settings.MEDIA_URL}{rel_file_path}"
#             download_url = request.build_absolute_uri(f"/media/{rel_file_path}")
#             accessible_files.append({
#                 "file_name": file_name,
#                 "can_view": True,
#                 "can_edit": True,
#                 "can_delete": True,
#                 "file_url": file_url,
#                 "download_url": download_url
#             })
#     else:
#         for file_name in all_files:
#             rel_file_path = os.path.join(rel_folder_path, file_name)
#             access = access_map.get(rel_file_path)

#             if access and access.can_view:
#                 file_url = f"{settings.MEDIA_URL}{rel_file_path}"
#                 download_url = request.build_absolute_uri(f"/media/{rel_file_path}")
#                 accessible_files.append({
#                     "file_name": file_name,
#                     "can_view": access.can_view,
#                     "can_edit": access.can_edit,
#                     "can_delete": access.can_delete,
#                     "file_url": file_url,
#                     "download_url": download_url
#                 })

#         # === List Folders ===
#         all_folders = [
#             d for d in os.listdir(abs_folder_path)
#             if os.path.isdir(os.path.join(abs_folder_path, d))
#         ]

#         # Full paths like test_folder_1/subfolder_name
#         full_folder_paths = [os.path.join(rel_folder_path, d) for d in all_folders]

#         # Fetch permissions for those folders
#         folder_access_records = FolderAccess.objects.filter(
#             user=user,
#             folder_path__in=full_folder_paths,
#             can_view=True
#         )

#         # Build a map for quick lookup
#         folder_access_map = {f.folder_path: f for f in folder_access_records}

#         # Prepare folder list with permissions
#         accessible_folders = []
#         for folder_name in all_folders:
#             folder_rel_path = os.path.join(rel_folder_path, folder_name)
#             access = folder_access_map.get(folder_rel_path)
#             if access:
#                 accessible_folders.append({
#                     "name": folder_name,
#                     "path": folder_rel_path,
#                     "can_view": access.can_view,
#                     "can_edit": access.can_edit,
#                     "can_delete": access.can_delete
#                 })

#         # === Final Response ===
#         return Response({
#             "folder_path": rel_folder_path,
#             "files": accessible_files,
#             "folders": accessible_folders
#         })


def get_files(request):
    user = request.user
    rel_folder_path = request.data.get("folder_path", "").strip()
    abs_folder_path = os.path.join(settings.MEDIA_ROOT, rel_folder_path)

    if not rel_folder_path or not os.path.isdir(abs_folder_path):
        return Response({errors.Error: errors.INVALID_FOLDER_PATH})

    # === List Files ===
    all_files = [
        f for f in os.listdir(abs_folder_path)
        if os.path.isfile(os.path.join(abs_folder_path, f))
    ]
    file_paths = [os.path.join(rel_folder_path, f) for f in all_files]

    accessible_files = []

    if is_admin(user):
        # Admin sees all files with full permissions
        for file_name in all_files:
            rel_file_path = os.path.join(rel_folder_path, file_name)
            file_url = f"{settings.MEDIA_URL}{rel_file_path}"
            download_url = request.build_absolute_uri(f"/media/{rel_file_path}")
            accessible_files.append({
                "file_name": file_name,
                "can_view": True,
                "can_edit": True,
                "can_delete": True,
                "can_download": True,
                "file_url": file_url,
                "download_url": download_url
            })
    else:
        access_records = FileAccess.objects.filter(user=user, file_path__in=file_paths)
        access_map = {record.file_path: record for record in access_records}

        for file_name in all_files:
            rel_file_path = os.path.join(rel_folder_path, file_name)
            access = access_map.get(rel_file_path)

            if access and access.can_view:
                file_url = f"{settings.MEDIA_URL}{rel_file_path}"
                download_url = request.build_absolute_uri(f"/media/{rel_file_path}")
                accessible_files.append({
                    "file_name": file_name,
                    "can_view": access.can_view,
                    "can_edit": access.can_edit,
                    "can_delete": access.can_delete,
                    "can_download": access.can_download,
                    "file_url": file_url,
                    "download_url": download_url
                })

    # === List Folders ===
    all_folders = [
        d for d in os.listdir(abs_folder_path)
        if os.path.isdir(os.path.join(abs_folder_path, d))
    ]

    full_folder_paths = [os.path.join(rel_folder_path, d) for d in all_folders]

    accessible_folders = []

    if is_admin(user):
        # Admin sees all subfolders with full permissions
        for folder_name in all_folders:
            folder_rel_path = os.path.join(rel_folder_path, folder_name)
            accessible_folders.append({
                "name": folder_name,
                "path": folder_rel_path,
                "can_view": True,
                "can_edit": True,
                "can_delete": True,
                "can_download": True,
            })
    else:
        folder_access_records = FolderAccess.objects.filter(
            user=user,
            folder_path__in=full_folder_paths,
            can_view=True
        )
        folder_access_map = {f.folder_path: f for f in folder_access_records}

        for folder_name in all_folders:
            folder_rel_path = os.path.join(rel_folder_path, folder_name)
            access = folder_access_map.get(folder_rel_path)
            if access:
                accessible_folders.append({
                    "name": folder_name,
                    "path": folder_rel_path,
                    "can_view": access.can_view,
                    "can_edit": access.can_edit,
                    "can_delete": access.can_delete,
                    "can_download": access.can_download,
                })

    return Response({
        "folder_path": rel_folder_path,
        "files": accessible_files,
        "folders": accessible_folders
    })


def download(request):
    folder_path = request.data.get("folder_path")
    if not folder_path:
        return Response({errors.Error: errors.PATH_NOT_PROVIDED})

    abs_folder_path = os.path.join(settings.MEDIA_ROOT, folder_path)
    # if not os.path.exists(abs_folder_path) or not os.path.isdir(abs_folder_path):
    #     raise Http404("Folder not found")
    if not FolderAccess.objects.filter(folder_path=folder_path, user=request.user).exists():
        raise Http404("Folder not found in database")
    
    access = FolderAccess.objects.filter(folder_path=folder_path, user=request.user).first()
    if not access or not access.can_download:
        return Response({errors.Error: errors.DOWNLOAD_PERMISSION})

    # Create zip in memory
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
        return Response({errors.Error: errors.MISSING__OLDPATH})
    elif not new_name:
        return Response({errors.Error: errors.MISSING_NEWNAME})

    # Strip '/media/' only if present in the path
    # if old_path.startswith('/media/'):
    #     relative_path = old_path[len('/media/'):]  # remove '/media/'
    # else:
    #     relative_path = old_path  # assume already relative
    relative_path = old_path
    abs_old_path = os.path.join(settings.MEDIA_ROOT, relative_path)
    dir_name = os.path.dirname(abs_old_path)
    abs_new_path = os.path.join(dir_name, new_name)

    if not os.path.exists(abs_old_path):
        return Response({errors.Error: f"Item does not exist at: {abs_old_path}"})

    try:
        os.rename(abs_old_path, abs_new_path)
    except Exception as e:
        return Response({errors.Error: str(e)})

    rel_new_path = os.path.join(os.path.dirname(relative_path), new_name)

    if os.path.isdir(abs_new_path):
        FolderAccess.objects.filter(folder_path=relative_path).update(folder_path=rel_new_path)
    else:
        FileAccess.objects.filter(file_path=relative_path).update(file_path=rel_new_path)

    return Response({"message": "Renamed successfully", "new_path": rel_new_path})


def delete_file_folder(request):
    path = request.data.get('path')

    if not path:
        return Response({errors.Error: errors.PATH_NOT_PROVIDED})

    # Convert /media/... to relative path
    relative_path = path.replace('/media/', '')
    abs_path = os.path.join(settings.MEDIA_ROOT, relative_path)

    if not os.path.exists(abs_path):
        return Response({errors.Error: errors.PATH_DOES_NOT_EXIST})

    try:
        if os.path.isdir(abs_path):
            shutil.rmtree(abs_path)
            FolderAccess.objects.filter(folder_path=relative_path).delete()
        else:
            os.remove(abs_path)
            FileAccess.objects.filter(file_path=relative_path).delete()
    except Exception as e:
        return Response({errors.Error: str(e)})

    return Response({errors.Success: errors.DELETED_SUCCESSFULLY})


def trash(request):
    try:
        print('req.data is', request.data)

        path = request.data.get("path")
        if path.startswith("/media/"):
            path = path[len("/media/"):]
        item_type = request.data.get("type")
        print('item type is:', item_type)
        print('path is:', path)

        now = timezone.now()
        updated = []

        if item_type == "file":
            file = FileAccess.objects.filter(file_path=path).first()
            print('file is: ', file)
            if file:
                file.is_trashed = True
                file.trashed_at = now
                file.save()
                updated.append('/media/' + file.file_path)
            else:
                return Response({errors.Error: errors.FILE_NOT_FOUND})

        elif item_type == "folder":
            folder = FolderAccess.objects.filter(folder_path=path).first()
            if folder:
                folder.is_trashed = True
                folder.trashed_at = now
                folder.save()
                updated.append('/media/' + folder.folder_path)
            else:
                return Response({errors.Error: errors.FOLDER_NOT_FOUND})

        else:
            return Response({errors.Error: errors.INVALID_TYPE})

        return Response({
            errors.Success: True,
            "updated": updated
        })

    except Exception as e:
        return Response({"error": str(e)})


def get_trash(request):
    user = request.user
    if is_admin(user):
        folders = FolderAccess.objects.filter(is_trashed=True)
        folders = FolderAccessSerializer(folders, many=True).data
        for folder in folders:
            folder["folder_path"] = "/media/" + folder["folder_path"]
        print('folders: ', folders)
        files = FileAccess.objects.filter(is_trashed=True)
        files = FileAccessSerializer(files, many=True).data
        for file in files:
            file["file_path"] = "/media/" + file["file_path"]
        print('files: ', files)
        return Response({
            errors.Success: "Trash",
            "folders": folders,
            "files": files,
            })
    else:
        return Response({errors.Error: errors.UNAUTHORIZED})

def create_folder(request):
    name = request.data.get('name')
    path = request.data.get('path') or '.'
    clean_path = os.path.join(path, name)
    if clean_path.startswith('./'):
        clean_path = clean_path[2:]

    abs_parent_path = os.path.join(settings.MEDIA_ROOT, path)
    abs_new_path = os.path.join(abs_parent_path, name)
    if FolderAccess.objects.filter(folder_path=clean_path).exists():
        return Response({errors.Error: errors.FOLDER_ALREADY_EXISTS})

    if os.path.exists(abs_new_path):
        print("Folder exists on disk but not in DB. Re-using it.")

    try:
        os.makedirs(abs_new_path, exist_ok=True)
        FolderAccess.objects.create(
            folder_path=clean_path,
            user=request.user,
            can_view=True,
            can_edit=False,
            can_delete=False
        )
        return Response({errors.Success: errors.FOLDER_CREATED_SUCCESSFULLY})

    except Exception as e:
        return Response({errors.Error: str(e)})


def upload_file(request):
    print('inside create file')

    uploaded_file = request.FILES.get('file')
    upload_path = request.POST.get('path') or ''

    print('uploaded file:', uploaded_file)
    print('uploaded path:', upload_path)

    if not uploaded_file:
        return Response({errors.Error: errors.MISSING_FILE})

    # Handle empty path case
    if upload_path.strip() == '':
        dest_dir = settings.MEDIA_ROOT  # Save to base directory
        db_path = uploaded_file.name  # Save only file name in DB path
    else:
        dest_dir = os.path.join(settings.MEDIA_ROOT, upload_path)
        db_path = os.path.join(upload_path, uploaded_file.name)

    # Make sure destination folder exists
    os.makedirs(dest_dir, exist_ok=True)

    # Save file to destination path
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
    )
    return Response({errors.Success: errors.FILE_UPLOADED_SUCCESSFULLY})


def upload_fol(request):

    uploaded_files = request.FILES.getlist('files')
    relative_paths = request.POST.getlist('paths')
    base_path = request.POST.get('base_path', '').strip()
    print('relative paths: ', relative_paths)
    print('base path: ', base_path)
    folder_paths_set = set()

    for i, file in enumerate(uploaded_files):
        print('inside for loop')
        rel_path = relative_paths[i] if i < len(relative_paths) else file.name
        full_path = os.path.join(base_path, rel_path)
        abs_path = os.path.join(settings.MEDIA_ROOT, full_path)
        print('full path is: ', full_path)
        print('abs path: ', abs_path)
        print('→ Saving to:', full_path)

        # Create parent folders
        parent_folder_path = os.path.dirname(full_path)
        print('parent folder: ', parent_folder_path)
        while parent_folder_path and parent_folder_path not in folder_paths_set:
            abs_folder = os.path.join(settings.MEDIA_ROOT, parent_folder_path)
            os.makedirs(abs_folder, exist_ok=True)
            folder_paths_set.add(parent_folder_path)

            FolderAccess.objects.get_or_create(
                folder_path=parent_folder_path,
                defaults={
                    'user': request.user,
                    'can_view': True,
                    'can_edit': True,
                    'can_delete': True,
                    'can_download': True
                }
            )
            parent_folder_path = os.path.dirname(parent_folder_path)

        # Save file
        with open(abs_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        FileAccess.objects.create(
            file_path=full_path,
            user=request.user,
            can_view=True,
            can_edit=True,
            can_delete=True,
            can_download=True
        )

    return Response({"message": "Folder uploaded successfully"})


def users(request):
    if request.user.role == 'admin' or request.user.role == 'Admin':
        users = User.objects.all().values('username')
        return Response({"users": users})
    else:
        return Response({"Error":"User is not admin"})
    

def folders(request):
    folders = FolderAccess.objects.values_list('folder_path', flat=True).distinct()
    top_level_folders = [path for path in folders if '/' not in path and '\\' not in path]
    return Response({
        "folders": [{"folder_path": path} for path in top_level_folders]
    })


def folder_access(request):
    print('inside folder access middleware')

    for item in request.data:
        usernames = item.get("username", [])
        folder_paths = item.get("folder_path", [])
        can_upload_folder = item.get("can_upload_folder")
        can_upload_file = item.get("can_upload_file")
        can_view = item.get("can_view")
        can_edit = item.get("can_edit")
        can_delete = item.get("can_delete")
        can_download = item.get("can_download")

    print('after for loop')

    if isinstance(usernames, str):
        usernames = [usernames]
    if isinstance(folder_paths, str):
        folder_paths = [folder_paths]

    if not User.objects.filter(username__in=usernames).exists():
        return Response({errors.Error: errors.SELECTED_USER_DOES_NOT_EXIST})
    if not folder_paths and (can_view or can_edit or can_delete or can_download):
        return Response({errors.Error: errors.PATH_NOT_PROVIDED})

    updated_objs = []

    for username in usernames:
        user = User.objects.get(username=username)
        try:
            user_perm, created = UserPermissions.objects.get_or_create(user=user)
            user_perm.can_upload_folder = can_upload_folder
            user_perm.can_upload_file = can_upload_file
            user_perm.save()
        except Exception as e:
            return Response({errors.Error: f"Error updating permissions for {username}: {e}"})
        for folder_path in folder_paths:
            # Assign folder-level access
            obj, created = FolderAccess.objects.get_or_create(
                user=user,
                folder_path=folder_path,
                defaults={
                    'can_view': can_view,
                    'can_edit': can_edit,
                    'can_delete': can_delete,
                    'can_download': can_download,
                }
            )
            if not created:
                obj.can_view = can_view
                obj.can_edit = can_edit
                obj.can_delete = can_delete
                obj.can_download = can_download
            updated_objs.append(obj)

            # Grant access to files/subfolders within the folder
            full_folder_path = os.path.join(settings.MEDIA_ROOT, folder_path)
            if os.path.exists(full_folder_path):
                for item in os.listdir(full_folder_path):
                    if not item.startswith('.'):  # skip hidden
                        item_path = os.path.join(folder_path, item)  # relative path
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

    # Save updated folder access records
    if len(updated_objs) == 1:
        updated_objs[0].save()
    elif len(updated_objs) > 1:
        FolderAccess.objects.bulk_update(updated_objs, ['can_view', 'can_edit', 'can_delete', 'can_download'])

    return Response({"message": f"Permissions assigned to {len(updated_objs)} folder records, and their files."})


def get_user_upload_permissions(request):
    user=request.user
    if not user:
        return Response({errors.Error: errors.USER_NOT_PROVIDED})
    try:
        if not UserPermissions.objects.filter(user=user).exists():
            return Response({errors.Error: errors.USER_DOES_NOT_EXIST})
        permissions = UserPermissions.objects.get(user=user)
        return Response({
            "can_upload_folder": permissions.can_upload_folder,
            "can_upload_file": permissions.can_upload_file
        })
    except UserPermissions.DoesNotExist:
        return Response({
            "can_upload_folder": False,
            "can_upload_file": False
        })