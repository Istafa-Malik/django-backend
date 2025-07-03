import os
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .models import FolderAccess, FileAccess
from django.contrib.auth import login
from .serializers import LoginSerializer
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import ensure_csrf_cookie
from .middleware import get_folders, get_file_access, list_folder_files
from django.middleware.csrf import get_token
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken


@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({'message': 'CSRF cookie set'})

@api_view(['POST'])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            "message": "Login successful",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            })
    return Response(serializer.errors)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_folders(request):
   return get_folders(request)

    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def file_access(request):
    return get_file_access(request)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def list_files(request):
    return list_folder_files(request)


