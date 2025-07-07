import os
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .serializers import LoginSerializer
from rest_framework.permissions import IsAuthenticated
from .middleware import get_folders, get_files, download, rename
from rest_framework_simplejwt.tokens import RefreshToken


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