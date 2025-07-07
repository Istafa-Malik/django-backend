import os
from rest_framework.response import Response
from .models import FolderAccess, FileAccess
from django.conf import settings
from django.http import FileResponse, HttpResponseBadRequest, Http404
import zipfile
import io


def get_folders(request):
    user = request.user
    folders = []
    access_entries = FolderAccess.objects.filter(user=user, can_view=True)
    
    if not access_entries.exists():
        return Response({"error": "You do not have access to any folders."})
    
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

                                            #Following function can be used as a specific access/permission function for a better code structure
                                            #for now I have commented it.


# def get_file_access(request):
#     user = request.user
#     rel_file_path = request.data.get("file_path", "").strip()
#     abs_file_path = os.path.join(settings.BASE_DIR, rel_file_path)

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



def get_files(request):
    user = request.user
    rel_folder_path = request.data.get("folder_path", "").strip()

    if not rel_folder_path:
        return Response({"error": "Folder path not provided."})

    abs_folder_path = os.path.join(settings.BASE_DIR, rel_folder_path)
    if not os.path.isdir(abs_folder_path):
        return Response({"error": "Invalid folder path."})

    all_files = [
        f for f in os.listdir(abs_folder_path)
        if os.path.isfile(os.path.join(abs_folder_path, f))
    ]

    file_paths = [os.path.join(rel_folder_path, f) for f in all_files]
    print('file paths: ', file_paths)
    access_records = FileAccess.objects.filter(user=user, file_path__in=file_paths)
    
    access_map = {record.file_path: record for record in access_records}
    print('access map: ',access_map)
    accessible_files = []
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
                "file_url": file_url,
                "download_url": download_url
            })

    return Response({
        "folder_path": rel_folder_path,
        "files": accessible_files
    })


def download(request):
    folder_path = request.data.get("folder_path")
    if not folder_path:
        return Response({"error": "No folder path provided"}, status=400)

    abs_folder_path = os.path.join(settings.BASE_DIR, folder_path)
    if not os.path.exists(abs_folder_path) or not os.path.isdir(abs_folder_path):
        raise Http404("Folder not found")

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

    if not old_path or not new_name:
        return Response({'error': 'Missing old_path or new_name'})

    abs_old_path = os.path.join(settings.BASE_DIR, old_path)
    dir_name = os.path.dirname(abs_old_path)
    abs_new_path = os.path.join(dir_name, new_name)

    new_rel_path = os.path.join(os.path.dirname(old_path), new_name)

    try:
        # 1. Rename the file or folder in the file system
        os.rename(abs_old_path, abs_new_path)

        # 2. Update database paths
        FileAccess.objects.filter(file_path=old_path).update(file_path=new_rel_path)

        return Response({'message': 'Renamed successfully'})
    except Exception as e:
        return Response({'error': str(e)})