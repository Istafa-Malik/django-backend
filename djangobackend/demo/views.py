import os
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .models import FolderAccess, FileAccess
from django.contrib.auth import login
from .serializers import LoginSerializer
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .middleware import get_folders, get_file_access

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
   return get_folders(request)

    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def list_files(request):
    return get_file_access(request)

