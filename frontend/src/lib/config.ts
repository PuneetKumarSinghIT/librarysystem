// Centralized API configuration and endpoint paths.
// All request URLs are built from here — no endpoint strings live in the app code.

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const TOKEN_KEY = "library_access_token";
export const STAFF_KEY = "library_staff";

/** Default page size for server-side pagination across list views. */
export const PAGE_SIZE = 10;

/** Every REST endpoint the frontend talks to, in one place. */
export const ENDPOINTS = {
  auth: {
    login: "/auth/login",
    refresh: "/auth/refresh",
    logout: "/auth/logout",
  },
  books: {
    root: "/books",
    byId: (id: string) => `/books/${id}`,
    copies: (id: string) => `/books/${id}/copies`,
  },
  members: {
    root: "/members",
    byId: (id: string) => `/members/${id}`,
  },
  loans: {
    root: "/loans",
    return: (id: string) => `/loans/${id}/return`,
  },
} as const;
