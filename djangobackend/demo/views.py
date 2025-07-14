import os
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .serializers import LoginSerializer
from rest_framework.permissions import IsAuthenticated
from .middleware import get_folders, get_files, download, rename, delete_file_folder, create_file, upload_fol, create_folder
from rest_framework_simplejwt.tokens import RefreshToken


@api_view(['POST'])
def login(request):
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    print('logout')
    try:
        print('req body is: ', request.data)
        refresh_token = request.data.get("refresh")
        if refresh_token is None:
            return Response({"error": "Refresh token is required"})
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"detail": "Logout successful"})
    except Exception as e:
        return Response({"error": str(e)})