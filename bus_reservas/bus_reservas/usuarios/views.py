"""
Views de la aplicación USUARIOS.

Endpoints para autenticación JWT personalizada con claims de rol,
registro de usuarios y gestión de perfil.
"""

from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema, OpenApiResponse

from django.contrib.auth import get_user_model
from .serializers import (
    CambioPasswordSerializer,
    CustomTokenObtainPairSerializer,
    LogoutSerializer,
    MensajeSerializer,
    RegistroUsuarioSerializer,
    UsuarioSerializer,
)

Usuario = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista personalizada para login con JWT.
    
    Retorna access token, refresh token y datos del usuario con rol.
    Endpoint: POST /api/login/
    """
    serializer_class = CustomTokenObtainPairSerializer


class RegistroUsuarioView(generics.CreateAPIView):
    """
    Vista para registro de nuevos usuarios.
    
    Crea un usuario con rol PASAJERO por defecto.
    Endpoint: POST /api/login/registro/
    """
    queryset = Usuario.objects.all()
    serializer_class = RegistroUsuarioSerializer
    permission_classes = [AllowAny]


class PerfilUsuarioView(generics.RetrieveUpdateAPIView):
    """
    Vista para ver y actualizar perfil del usuario autenticado.
    
    Endpoints:
    - GET /api/login/perfil/ - Ver perfil
    - PUT/PATCH /api/login/perfil/ - Actualizar perfil
    """
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class CambioPasswordView(generics.GenericAPIView):
    """
    Vista para cambio de contraseña del usuario autenticado.
    
    Endpoint: POST /api/login/cambio-password/
    """
    serializer_class = CambioPasswordSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        if not user.check_password(serializer.validated_data['password_actual']):
            return Response(
                {'password_actual': 'La contraseña actual es incorrecta.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(serializer.validated_data['password_nuevo'])
        user.save()
        
        return Response({'detail': 'Contraseña actualizada correctamente.'})


@extend_schema(
    request=LogoutSerializer,
    responses={
        200: MensajeSerializer,
        400: OpenApiResponse(description='El refresh token es inválido o expiró.'),
    },
    description='Invalida el refresh token para cerrar la sesión JWT.',
)
@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    """
    Vista para logout (blacklist del refresh token).
    
    Endpoint: POST /api/login/logout/
    """
    serializer = LogoutSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    refresh_token = serializer.validated_data.get('refresh')
    if refresh_token:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {'detail': 'Token inválido o ya expirado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    return Response({'detail': 'Sesión cerrada correctamente.'})