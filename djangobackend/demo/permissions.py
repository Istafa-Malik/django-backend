from .models import FolderAccess, FileAccess, UserPermissions
from rest_framework.response import Response
from demo import errors

#                                                           Admin

def is_admin(user):
    return user.role == 'admin' or user.role == 'Admin'



#                                                       Folders permissions



def can_view_folder(user, folder_path):
    if is_admin(user):
        return True
    return FolderAccess.objects.filter(user=user, folder_path=folder_path, can_view=True).exists()

def can_rename_folder(user, folder_path):
    if is_admin(user):
        return True
    return FolderAccess.objects.filter(user=user, folder_path=folder_path, can_edit=True).exists()

def can_delete_folder(user, folder_path):
    if is_admin(user):
        return True
    return FolderAccess.objects.filter(user=user, folder_path=folder_path, can_delete=True).exists()

def can_download_folder(user, folder_path):
    if is_admin(user):
        return True
    return FolderAccess.objects.filter(user=user, folder_path=folder_path, can_download=True).exists()

#                                                       Files permissions


def can_view_file(user, file_path):
    if is_admin(user):
        return True
    return FileAccess.objects.filter(user=user, file_path=file_path, can_view=True).exists()

def can_rename_file(user, file_path):
    if is_admin(user):
        return True
    return FileAccess.objects.filter(user=user, file_path=file_path, can_edit=True).exists()


def can_delete_file(user, file_path):
    if is_admin(user):
        return True
    return FileAccess.objects.filter(user=user, file_path=file_path, can_delete=True).exists()



#                                                                   User permissions



def check_permission(action):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            permissions = UserPermissions.objects.filter(user=request.user).first()
            if not permissions:
                return Response({errors.Error: errors.PERMISSIONS_NOT_SET})
            
            allowed = getattr(permissions, f"can_{action}", False)
            if not allowed:
                return Response({errors.Error: f"Permission denied for {action}"})

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
