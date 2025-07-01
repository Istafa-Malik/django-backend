import os
from rest_framework.response import Response
from .models import FolderAccess, FileAccess
from django.conf import settings


def get_folders(request):
    user = request.user
    folders = []

    access_entries = FolderAccess.objects.filter(user=user, can_view=True)
    
    if not access_entries.exists():
        return Response({"error": "You do not have access to any folders."}, status=403)
    
    for entry in access_entries:
        rel_folder_path = entry.folder_path
        abs_folder_path = os.path.join(settings.BASE_DIR, rel_folder_path)

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
            "can_view": entry.can_view,
            "can_edit": entry.can_edit,
            "can_delete": entry.can_delete,
            "subfolders": subfolders
        })

    return Response({"folders": folders})


def get_file_access(request):
    user = request.user
    rel_file_path = request.data.get("file_path", "").strip()
    abs_file_path = os.path.join(settings.BASE_DIR, rel_file_path)

    if not os.path.isfile(abs_file_path):
        return Response({"error": f"{rel_file_path} is not a valid file."}, status=400)

    try:
        access = FileAccess.objects.get(user=user, file_path=rel_file_path, can_view=True)
    except FileAccess.DoesNotExist:
        return Response({"error": "You do not have permission to view this file."}, status=403)

    return Response({
        "file_path": rel_file_path,
        "can_view": access.can_view,
        "can_edit": access.can_edit,
        "can_delete": access.can_delete,
        "file_url": f"/{rel_file_path}"
    })