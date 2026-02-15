from django.middleware.csrf import get_token
from django.conf import settings
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

# views.py
enProduccion = not settings.DEBUG


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access_token = response.data.get("access")
            refresh_token = response.data.get("refresh")

            # 1. Forzamos la generación del CSRF token para este usuario
            csrf_token = get_token(request)

            # 2. Seteamos la cookie de Access Token
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=enProduccion,
                samesite="Lax",
                path="/",
            )

            # 3. Seteamos la cookie de Refresh Token
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=enProduccion,
                samesite="Lax",
                path="/",
            )

            # 4. Seteamos la cookie CSRF explícitamente (NO HttpOnly)
            # El frontend necesita leerla para enviarla en el header X-CSRFToken
            response.set_cookie(
                key="csrftoken",
                value=csrf_token,
                httponly=False,  # DEBE ser False para que JS la lea
                secure=enProduccion,
                samesite="Lax",
                path="/",
            )

            # Agregamos el token al body solo esta vez para facilitar al front
            # o simplemente dejamos que el front lo lea de la cookie.

            del response.data["access"]
            del response.data["refresh"]

        return response


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        # Extraemos el refresh token de la cookie
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token:
            # Lo inyectamos en los datos de la petición para que SimpleJWT lo vea
            request.data["refresh"] = refresh_token

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access_token = response.data.get("access")

            # Seteamos el nuevo access token en la cookie
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=enProduccion,
                samesite="Lax",
                path="/",
            )
            # Limpiamos el JSON
            del response.data["access"]

        return response


class LogoutView(APIView):
    def post(self, request):
        response = Response(
            {"detail": "Sesión cerrada exitosamente"}, status=status.HTTP_200_OK
        )

        # Borrar el csrftoken
        if "csrftoken" in request.COOKIES:
            response.delete_cookie("csrftoken")

        # Borramos la cookie del navegador
        if "access_token" in request.COOKIES:
            response.delete_cookie(settings.SIMPLE_JWT["AUTH_COOKIE"])

        # Si también usas Refresh Tokens en cookies, bórralo aquí
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token:
            # Esto añade el token a la lista negra en la DB
            token = RefreshToken(refresh_token)
            token.blacklist()

            response.delete_cookie("refresh_token")

        return response
