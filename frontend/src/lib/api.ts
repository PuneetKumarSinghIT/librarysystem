// Typed client for the Neighborhood Library REST API.
// Endpoint paths and base URL are centralized in lib/config.

import { API_BASE, ENDPOINTS, PAGE_SIZE, TOKEN_KEY } from "./config";

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

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  } catch {
    throw new ApiError(0, "network_error", "Cannot reach the server. Is the API running?");
  }
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
export interface Paged<T> { items: T[]; page: Page }

export interface PageParams { limit?: number; offset?: number }

function pageQuery(params: PageParams): URLSearchParams {
  const q = new URLSearchParams();
  q.set("limit", String(params.limit ?? PAGE_SIZE));
  q.set("offset", String(params.offset ?? 0));
  return q;
}

export const api = {
  login: (email: string, password: string) =>
    request<TokenResponse>(ENDPOINTS.auth.login, {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  // ── Books ──
  listBooks: (params: PageParams & { search?: string } = {}) => {
    const q = pageQuery(params);
    if (params.search) q.set("search", params.search);
    return request<Paged<Book>>(`${ENDPOINTS.books.root}?${q.toString()}`);
  },
  createBook: (data: Partial<Book>) =>
    request<Book>(ENDPOINTS.books.root, { method: "POST", body: JSON.stringify(data) }),
  updateBook: (id: string, changes: Partial<Book>) =>
    request<Book>(ENDPOINTS.books.byId(id), { method: "PATCH", body: JSON.stringify(changes) }),
  addCopy: (bookId: string, barcode: string, condition?: string) =>
    request<Copy>(ENDPOINTS.books.copies(bookId), {
      method: "POST",
      body: JSON.stringify({ barcode, condition }),
    }),
  listCopies: (bookId: string) => request<Copy[]>(ENDPOINTS.books.copies(bookId)),

  // ── Members ──
  listMembers: (params: PageParams & { search?: string } = {}) => {
    const q = pageQuery(params);
    if (params.search) q.set("search", params.search);
    return request<Paged<Member>>(`${ENDPOINTS.members.root}?${q.toString()}`);
  },
  createMember: (data: Partial<Member>) =>
    request<Member>(ENDPOINTS.members.root, { method: "POST", body: JSON.stringify(data) }),
  updateMember: (id: string, changes: Partial<Member>) =>
    request<Member>(ENDPOINTS.members.byId(id), {
      method: "PATCH",
      body: JSON.stringify(changes),
    }),
  deleteMember: (id: string) =>
    request<{ success: boolean }>(ENDPOINTS.members.byId(id), { method: "DELETE" }),

  // ── Loans ──
  listLoans: (params: PageParams & { member_id?: string; active_only?: boolean } = {}) => {
    const q = pageQuery(params);
    if (params.member_id) q.set("member_id", params.member_id);
    if (params.active_only) q.set("active_only", "true");
    return request<Paged<Loan>>(`${ENDPOINTS.loans.root}?${q.toString()}`);
  },
  borrow: (member_id: string, copy_id?: string, book_id?: string) =>
    request<Loan>(ENDPOINTS.loans.root, {
      method: "POST",
      body: JSON.stringify({ member_id, copy_id, book_id }),
    }),
  returnLoan: (loanId: string) =>
    request<Loan>(ENDPOINTS.loans.return(loanId), { method: "POST" }),
};
