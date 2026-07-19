// Typed client for the Neighborhood Library REST API.

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const TOKEN_KEY = "library_access_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  code: string;
  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (res.status === 204) return undefined as T;

  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = body?.error ?? {};
    throw new ApiError(res.status, err.code ?? "error", err.message ?? res.statusText);
  }
  return body as T;
}

// ── Types ──
export interface Staff { id: string; email: string; role: string; is_active: boolean }
export interface TokenResponse { access_token: string; refresh_token: string; expires_in: number; staff: Staff }
export interface Book {
  id: string; title: string; author: string; isbn: string | null; publisher: string | null;
  published_year: number | null; category: string | null; description: string | null;
  total_copies: number; available_copies: number;
}
export interface Copy { id: string; book_id: string; barcode: string; condition: string; status: string }
export interface Member {
  id: string; first_name: string; last_name: string; email: string;
  phone: string | null; address: string | null; status: string;
}
export interface Loan {
  id: string; copy_id: string; book_id: string; book_title: string; barcode: string;
  member_id: string; member_name: string; borrowed_at: string; due_at: string;
  returned_at: string | null; status: string; renewed_count: number;
}
export interface Page { limit: number; offset: number; total: number }

export const api = {
  login: (email: string, password: string) =>
    request<TokenResponse>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),

  listBooks: (search = "") =>
    request<{ items: Book[]; page: Page }>(`/books?search=${encodeURIComponent(search)}&limit=100`),
  createBook: (data: Partial<Book>) =>
    request<Book>("/books", { method: "POST", body: JSON.stringify(data) }),
  addCopy: (bookId: string, barcode: string, condition?: string) =>
    request<Copy>(`/books/${bookId}/copies`, { method: "POST", body: JSON.stringify({ barcode, condition }) }),
  listCopies: (bookId: string) => request<Copy[]>(`/books/${bookId}/copies`),

  listMembers: (search = "") =>
    request<{ items: Member[]; page: Page }>(`/members?search=${encodeURIComponent(search)}&limit=100`),
  createMember: (data: Partial<Member>) =>
    request<Member>("/members", { method: "POST", body: JSON.stringify(data) }),

  listLoans: (params: { member_id?: string; active_only?: boolean } = {}) => {
    const q = new URLSearchParams();
    if (params.member_id) q.set("member_id", params.member_id);
    if (params.active_only) q.set("active_only", "true");
    q.set("limit", "100");
    return request<{ items: Loan[]; page: Page }>(`/loans?${q.toString()}`);
  },
  borrow: (member_id: string, copy_id?: string, book_id?: string) =>
    request<Loan>("/loans", { method: "POST", body: JSON.stringify({ member_id, copy_id, book_id }) }),
  returnLoan: (loanId: string) => request<Loan>(`/loans/${loanId}/return`, { method: "POST" }),
};
