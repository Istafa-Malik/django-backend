import os
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .models import FolderAccess
from django.contrib.auth import login
from .serializers import LoginSerializer
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

@csrf_exempt
@api_view(['POST'])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        login(request, user)
        return Response({"message": "Login successful"})
    return Response(serializer.errors)
    


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_folders(request):
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
        except Exception as e:
            subfolders = []

        folders.append({
            "folder_path": rel_folder_path,
            "can_view": entry.can_view,
            "can_edit": entry.can_edit,
            "can_delete": entry.can_delete,
            "subfolders": subfolders
        })

    return Response({"folders": folders})

    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def list_files(request):
    user = request.user
    rel_folder_path = request.data.get("folder_path")
    try:
        access = FolderAccess.objects.get(user=user, folder_path=rel_folder_path, can_view=True)
    except FolderAccess.DoesNotExist:
        return Response({"error": "You do not have permission to view this folder."})
    
    try:
        abs_folder_path = os.path.join(settings.BASE_DIR, rel_folder_path)
        all_files = os.listdir(abs_folder_path)
        visible_files = [
            f for f in all_files
            if os.path.isfile(os.path.join(abs_folder_path, f)) and not f.startswith('.')
        ]
    except Exception as e:
        return Response({"error": f"Unable to read folder: {str(e)}"})
    
    return Response({
        "folder_path": rel_folder_path,
        'can_view': access.can_view,
        "can_edit": access.can_edit,
        "can_delete": access.can_delete,
        "files": visible_files
    })

    