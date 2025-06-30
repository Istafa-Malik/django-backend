import os
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .models import FolderAccess
from django.contrib.auth import login
from .serializers import LoginSerializer
from rest_framework.permissions import IsAuthenticated


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
def user_files_view(request):
    user = request.user
    access_entries = FolderAccess.objects.filter(user=user, can_view=True)

    folder_data = []

    for access in access_entries:
        folder_path = access.folder_path
        try:
            files = os.listdir(folder_path)
            files = [
                f for f in files
                if os.path.isfile(os.path.join(folder_path, f)) and not f.startswith('.')
            ]
        except FileNotFoundError:
            files = []

        folder_data.append({
            'folder_path': folder_path,
            'can_edit': access.can_edit,
            'can_delete': access.can_delete,
            'files': files
        })

    return Response({'folders': folder_data})