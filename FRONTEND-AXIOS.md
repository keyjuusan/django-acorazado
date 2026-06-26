# Uso de JWT con Axios

Guía para consumir la API de Django Acorazado desde un frontend Next.js/React con TypeScript usando Axios.

## Instalación

```bash
npm install axios
```

## Configuración del Cliente

### Instancia de Axios

Configuración base con soporte CSRF nativo de Axios.

```ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  withCredentials: true,
  withXSRFToken: true,
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
  headers: { 'Content-Type': 'application/json' },
});

export default api;
```

| Opción | Por qué |
|--------|---------|
| `withCredentials: true` | Envía cookies http-only en cada request |
| `withXSRFToken: true` | Envía header CSRF incluso en cross-origin |
| `xsrfCookieName: 'csrftoken'` | Lee la cookie que setea Django |
| `xsrfHeaderName: 'X-CSRFToken'` | Header que Django espera |

### Interceptor de Refresh Automático

```ts
import type { InternalAxiosRequestConfig } from 'axios';

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        await api.post('/api/token/refresh/');
        return api(originalRequest);
      } catch {
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);
```

## Tipos

```ts
// types/index.ts

export interface User {
  url: string;
  username: string;
  email: string;
  groups: string[];
}

export interface Group {
  url: string;
  name: string;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface CreateUserPayload {
  username: string;
  email: string;
  password: string;
  groups?: string[];
}

export interface UpdateUserPayload {
  username?: string;
  email?: string;
  groups?: string[];
}

export interface CreateGroupPayload {
  name: string;
}
```

## API Service

### Auth

```ts
// services/auth.ts
import api from '@/lib/api';
import type { LoginPayload } from '@/types';

export async function login(payload: LoginPayload): Promise<void> {
  await api.post('/api/auth/login/', payload);
  // Backend setea las cookies: access_token, refresh_token, csrftoken
}

export async function logout(): Promise<void> {
  await api.post('/api/auth/logout/');
}

export async function refreshToken(): Promise<void> {
  await api.post('/api/token/refresh/');
}
```

### Usuarios

```ts
// services/usuarios.ts
import api from '@/lib/api';
import type { User, CreateUserPayload, UpdateUserPayload } from '@/types';

export async function listarUsuarios(): Promise<User[]> {
  try {
    const { data } = await api.get<User[]>('/api/usuarios/');
    return data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.detail || 'Error al listar usuarios');
    }
    throw error;
  }
}

export async function crearUsuario(payload: CreateUserPayload): Promise<User> {
  try {
    const { data } = await api.post<User>('/api/usuarios/', payload);
    return data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const mensajes = Object.values(error.response?.data ?? {}).flat().join(', ');
      throw new Error(mensajes || 'Error al crear usuario');
    }
    throw error;
  }
}

export async function obtenerUsuario(id: number): Promise<User> {
  const { data } = await api.get<User>(`/api/usuarios/${id}/`);
  return data;
}

export async function actualizarUsuario(id: number, payload: UpdateUserPayload): Promise<User> {
  const { data } = await api.put<User>(`/api/usuarios/${id}/`, payload);
  return data;
}

export async function eliminarUsuario(id: number): Promise<void> {
  await api.delete(`/api/usuarios/${id}/`);
}
```

### Grupos

```ts
// services/grupos.ts
import api from '@/lib/api';
import type { Group, CreateGroupPayload } from '@/types';

export async function listarGrupos(): Promise<Group[]> {
  const { data } = await api.get<Group[]>('/api/grupos/');
  return data;
}

export async function crearGrupo(payload: CreateGroupPayload): Promise<Group> {
  const { data } = await api.post<Group>('/api/grupos/', payload);
  return data;
}

export async function eliminarGrupo(id: number): Promise<void> {
  await api.delete(`/api/grupos/${id}/`);
}
```

## React Context de Autenticación

```tsx
// context/AuthContext.tsx
'use client';

import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import { login as loginApi, logout as logoutApi, refreshToken } from '@/services/auth';
import type { LoginPayload } from '@/types';

interface AuthContextType {
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const login = useCallback(async (payload: LoginPayload) => {
    await loginApi(payload);
    setIsAuthenticated(true);
  }, []);

  const logout = useCallback(async () => {
    await logoutApi();
    setIsAuthenticated(false);
  }, []);

  const checkAuth = useCallback(async () => {
    try {
      await refreshToken();
      setIsAuthenticated(true);
      return true;
    } catch {
      setIsAuthenticated(false);
      return false;
    }
  }, []);

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth debe usarse dentro de AuthProvider');
  return context;
}
```

## Componentes de Ejemplo

### LoginForm

```tsx
'use client';

import { useState, type FormEvent } from 'react';
import { useAuth } from '@/context/AuthContext';

export function LoginForm() {
  const { login } = useAuth();
  const [error, setError] = useState('');

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError('');

    const form = new FormData(e.currentTarget);

    try {
      await login({
        username: form.get('username') as string,
        password: form.get('password') as string,
      });
      window.location.href = '/dashboard';
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al iniciar sesión');
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input name="username" placeholder="Usuario" required />
      <input name="password" type="password" placeholder="Contraseña" required />
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <button type="submit">Ingresar</button>
    </form>
  );
}
```

### ProtectedRoute

```tsx
'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { checkAuth } = useAuth();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth().then((autenticado) => {
      if (!autenticado) {
        window.location.href = '/login';
      } else {
        setLoading(false);
      }
    });
  }, [checkAuth]);

  if (loading) return <p>Verificando sesión...</p>;
  return <>{children}</>;
}
```

### Lista de Usuarios

```tsx
'use client';

import { useEffect, useState } from 'react';
import { listarUsuarios, eliminarUsuario } from '@/services/usuarios';
import type { User } from '@/types';

export function UserList() {
  const [usuarios, setUsuarios] = useState<User[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    listarUsuarios()
      .then(setUsuarios)
      .catch((err) => setError(err.message));
  }, []);

  async function handleDelete(id: number) {
    try {
      await eliminarUsuario(id);
      setUsuarios((prev) => prev.filter((u) => !u.url.endsWith(`/${id}/`)));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al eliminar');
    }
  }

  if (error) return <p style={{ color: 'red' }}>{error}</p>;

  return (
    <ul>
      {usuarios.map((user) => (
        <li key={user.url}>
          {user.username} ({user.email})
          <button onClick={() => handleDelete(Number(user.url.split('/').filter(Boolean).pop()))}>
            Eliminar
          </button>
        </li>
      ))}
    </ul>
  );
}
```

## Resumen del flujo

| Paso | Descripción |
|------|-------------|
| Login | `POST /api/auth/login/` → backend setea cookies |
| Requests | Axios envía cookies + CSRF header automáticamente |
| Token expirado | Interceptor captura 401 → `POST /api/token/refresh/` → reintenta |
| Logout | `POST /api/auth/logout/` → blacklist + elimina cookies |

## Notas importantes

- `withCredentials: true` es **obligatorio** — sin esto el navegador no envía cookies http-only
- `withXSRFToken: true` es **obligatorio** para cross-origin (localhost:3000 → localhost:8000)
- El frontend **nunca** toca `access_token` ni `refresh_token` (son http-only)
- El interceptor de refresh evita redirigir al login en cada 401
- Los servicios con `try/catch` y `axios.isAxiosError` dan errores legibles al usuario
