import os
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .serializers import LoginSerializer
from rest_framework.permissions import IsAuthenticated
from .middleware import get_folders, get_files, download, rename, delete_file_folder, create_file, upload_fol, create_folder, login_user, logout_user

@api_view(['POST'])
def login(request):
    return login_user(request)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    return logout_user(request)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_folders(request):
   return get_folders(request)

    
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def file_access(request):
#     return get_file_access(request)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def list_files(request):
    return get_files(request)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def download_folder(request):
    return download(request)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit(request):
    return rename(request)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete(request):
    return delete_file_folder(request)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_folder(request):
    return upload_fol(request)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create(request):
    return create_file(request)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_fold(request):
    return create_folder(request)


    