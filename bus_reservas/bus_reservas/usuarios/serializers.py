"""
Serializers de la aplicación USUARIOS.

Transforman los datos del modelo Usuario para la API REST,
incluyendo registro, login y representación del usuario con roles.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import Group

Usuario = get_user_model()


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Usuario.
    
    Incluye el rol calculado basado en grupos de Django.
    No expone la contraseña en lecturas.
    """
    
    rol = serializers.SerializerMethodField()
    es_admin = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'rol', 'es_admin', 'date_joined', 'is_active'
        ]
        read_only_fields = ['id', 'date_joined', 'rol', 'es_admin']
    
    def get_rol(self, obj) -> str:
        """Retorna el rol del usuario (PASAJERO o ADMINISTRADOR)."""
        return obj.get_rol()
    
    def get_es_admin(self, obj) -> bool:
        """Retorna True si el usuario es administrador."""
        return obj.is_admin()


class RegistroUsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para registro de nuevos usuarios.
    
    Crea un usuario con rol PASAJERO por defecto y lo asigna al grupo correspondiente.
    """
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']
    
    def validate(self, attrs):
        """Valida que las contraseñas coincidan."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Las contraseñas no coinciden.'})
        return attrs
    
    def create(self, validated_data):
        """Crea el usuario y lo asigna al grupo PASAJERO por defecto."""
        validated_data.pop('password_confirm')
        user = Usuario.objects.create_user(**validated_data)
        
        # Asignar al grupo PASAJERO por defecto
        grupo_pasajero, _ = Group.objects.get_or_create(name='PASAJERO')
        user.groups.add(grupo_pasajero)
        
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado para obtener tokens JWT.
    
    Agrega claims personalizados al token de acceso:
    - username
    - user_id
    - rol (PASAJERO o ADMINISTRADOR)
    """
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Agregar claims personalizados
        token['username'] = user.username
        token['user_id'] = user.id
        token['rol'] = user.get_rol()
        
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Agregar información del usuario a la respuesta
        data['usuario'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'rol': self.user.get_rol(),
            'es_admin': self.user.is_admin(),
        }
        
        return data


class CambioPasswordSerializer(serializers.Serializer):
    """
    Serializer para cambio de contraseña del usuario autenticado.
    """
    
    password_actual = serializers.CharField(required=True)
    password_nuevo = serializers.CharField(required=True, min_length=8)
    password_nuevo_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['password_nuevo'] != attrs['password_nuevo_confirm']:
            raise serializers.ValidationError({'password_nuevo_confirm': 'Las contraseñas nuevas no coinciden.'})
        return attrs


class LogoutSerializer(serializers.Serializer):
    """Accepts the refresh token to blacklist when the user logs out."""

    refresh = serializers.CharField(required=False, allow_blank=False)


class MensajeSerializer(serializers.Serializer):
    """Message-only API response used by account operations."""

    detail = serializers.CharField()