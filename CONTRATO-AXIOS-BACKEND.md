# Contrato Axios ↔ Backend

Cómo Axios puede operar con cookies HttpOnly + CSRF sin que el frontend maneje tokens manualmente.

---

## 1. El contrato de cookies

| Cookie | HttpOnly | ¿Quién la setea? | ¿Quién la lee? | Propósito |
|--------|----------|-------------------|----------------|-----------|
| `access_token` | `True` | Backend (`core/views.py:25`) | Solo el backend (`core/authenticate.py:8`) | Autenticar cada request |
| `refresh_token` | `True` | Backend (`core/views.py:35`) | Solo el backend (`core/views.py:67`) | Obtener un nuevo access_token |
| `csrftoken` | `False` | Backend (`core/views.py:46`) | Axios (vía `xsrfCookieName`) + Backend | Verificar que el request fue intencional (CSRF) |

**Regla del contrato:** El backend expone una sola cookie al frontend (`csrftoken`) y solo para que Axios la devuelva como header. Las cookies con tokens JWT son invisibles para JavaScript.

---

## 2. Mapeo Axios ↔ Django

```ts
const api = axios.create({
  withCredentials: true,         // ← Browser: "envía cookies aunque sea cross-origin"
  withXSRFToken: true,           // ← Axios: "activa el lector automático de CSRF"
  xsrfCookieName: 'csrftoken',   // ← Axios: "la cookie CSRF se llama 'csrftoken'"
  xsrfHeaderName: 'X-CSRFToken', // ← Axios: "el header CSRF se llama 'X-CSRFToken'"
});
```

| Opción Axios | Contraparte Django | Por qué funciona |
|---|---|---|
| `withCredentials: true` | `CORS_ALLOW_CREDENTIALS = True` | El backend acepta credenciales cross-origin; el browser las envía |
| `withXSRFToken: true` | `CsrfViewMiddleware` | Django espera el token CSRF en el header `X-CSRFToken` |
| `xsrfCookieName: 'csrftoken'` | `CSRF_COOKIE_NAME = 'csrftoken'` (default) | Coincidencia exacta de nombre de cookie |
| `xsrfHeaderName: 'X-CSRFToken'` | `CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'` (default) | Django normaliza el header a `HTTP_X_CSRFTOKEN` internamente |

---

## 3. Lo que pasa detrás de escena

Flujo completo de un `api.get('/api/usuarios/')`:

```
Frontend (localhost:3000)                     Backend (localhost:8000)
         │                                          │
         │  GET /api/usuarios/                       │
         │─────────────────────────────────────────>│
         │                                          │
         │  [Browser inyecta automáticamente]       │
         │    Cookie: access_token=eyJ...            │
         │    Cookie: refresh_token=eyJ...           │
         │    Cookie: csrftoken=abc123               │
         │                                          │
         │  [Axios intercepta ANTES de enviar]      │
         │    1. Lee cookie "csrftoken" → "abc123"   │
         │    2. Agrega header:                      │
         │       X-CSRFToken: abc123                 │
         │                                          │
         │  Request final:                           │
         │    Cookie: access_token=eyJ...            │
         │    Cookie: refresh_token=eyJ...           │
         │    Cookie: csrftoken=abc123               │
         │    X-CSRFToken: abc123                    │
         │─────────────────────────────────────────>│
         │                                          │
         │  [Backend procesa]                       │
         │    1. CustomJWTAuthentication             │
         │       → request.COOKIES["access_token"]   │
         │       → valida JWT                       │
         │       → usuario autenticado              │
         │    2. CsrfViewMiddleware                  │
         │       → compara cookie csrftoken          │
         │         con header X-CSRFToken            │
         │       → match → request legítimo          │
         │                                          │
         │  200 OK  [usuarios]                       │
         │<─────────────────────────────────────────│
```

**Puntos clave:**
- El frontend nunca ejecuta `document.cookie` ni `localStorage.getItem` para los tokens JWT
- El browser inyecta las cookies automáticamente gracias a `withCredentials: true`
- Axios solo toca la cookie `csrftoken` (la única no HttpOnly)
- Todo el manejo de JWT ocurre en el servidor

---

## 4. Por qué fetch nativo no es suficiente

Con Axios, el frontend escribe:

```ts
await api.get('/api/usuarios/');
```

Con `fetch` nativo, el mismo nivel de seguridad requeriría:

```ts
async function authenticatedGet(url: string) {
  // 1. Leer CSRF token manualmente
  const csrfToken = document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];

  // 2. Enviar request con cookies + CSRF header
  const response = await fetch(url, {
    method: 'GET',
    credentials: 'include',          // equivalente a withCredentials
    headers: {
      'X-CSRFToken': csrfToken ?? '', // equivalente a xsrfHeaderName
    },
  });

  // 3. Manejar refresh manualmente si da 401
  if (response.status === 401) {
    const refreshResponse = await fetch('/api/token/refresh/', {
      method: 'POST',
      credentials: 'include',
      headers: { 'X-CSRFToken': csrfToken ?? '' },
    });

    if (refreshResponse.ok) {
      return authenticatedGet(url); // reintenta
    } else {
      window.location.href = '/login';
    }
  }

  return response.json();
}
```

| Aspecto | Axios | fetch nativo |
|---------|-------|-------------|
| Enviar cookies cross-origin | `withCredentials: true` | `credentials: 'include'` |
| Leer cookie CSRF | Automático con `xsrfCookieName` | Manual: `document.cookie.split('; ')...` |
| Enviar header CSRF | Automático con `xsrfHeaderName` | Manual: `headers: { 'X-CSRFToken': ... }` |
| Refresh automático | Interceptor de 10 líneas | Manual en cada request |
| Manejo de errores | `axios.isAxiosError(error)` | Manual: `if (!response.ok)` |

**Conclusión:** Se puede lograr el mismo nivel de seguridad con fetch nativo, pero requiere ~30 líneas de boilerplate que Axios abstrae en 4 opciones de configuración.

---

## 5. Conclusión

Axios funciona con este nivel de seguridad porque el backend fue diseñado para que así sea:

1. **El backend expone una cookie `csrftoken` con `httponly=False`** — la única cookie que el frontend necesita leer
2. **Las cookies JWT son `httponly=True`** — el frontend no puede ni debe tocarlas
3. **Axios implementa `withXSRFToken`** — que es exactamente el patrón que Django espera: leer cookie → enviar header
4. **`CustomJWTAuthentication` lee el token de `request.COOKIES`** — la autenticación ocurre en el servidor

El contrato se resume en una frase: **el frontend solo toca la cookie CSRF; el backend y el browser se encargan del resto.**
