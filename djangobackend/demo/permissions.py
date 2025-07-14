from models import FolderAccess, FileAccess



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