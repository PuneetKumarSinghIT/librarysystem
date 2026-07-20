import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "./api";
import { API_BASE, TOKEN_KEY } from "./config";

function mockFetch(body: unknown = {}, ok = true, status = 200) {
  const fn = vi.fn().mockResolvedValue({ ok, status, json: async () => body });
  // @ts-expect-error test stub
  global.fetch = fn;
  return fn;
}

const lastCall = (f: ReturnType<typeof vi.fn>) => f.mock.calls[0];
const optsOf = (f: ReturnType<typeof vi.fn>) => lastCall(f)[1] as RequestInit;
const bodyOf = (f: ReturnType<typeof vi.fn>) => JSON.parse(optsOf(f).body as string);

describe("api client", () => {
  beforeEach(() => localStorage.clear());

  it("login POSTs to the centralized /auth/login endpoint", async () => {
    const f = mockFetch({ access_token: "t" });
    await api.login("a@b.com", "pw");
    expect(lastCall(f)[0]).toBe(`${API_BASE}/auth/login`);
    expect(optsOf(f).method).toBe("POST");
    expect(bodyOf(f)).toEqual({ email: "a@b.com", password: "pw" });
  });

  it("listBooks sends server-side pagination + search params", async () => {
    const f = mockFetch({ items: [], page: { limit: 10, offset: 20, total: 0 } });
    await api.listBooks({ search: "code", limit: 10, offset: 20 });
    const url = lastCall(f)[0] as string;
    expect(url).toContain("/books?");
    expect(url).toContain("limit=10");
    expect(url).toContain("offset=20");
    expect(url).toContain("search=code");
  });

  it("updateBook PATCHes /books/{id}", async () => {
    const f = mockFetch({});
    await api.updateBook("abc", { title: "New" });
    expect(lastCall(f)[0]).toBe(`${API_BASE}/books/abc`);
    expect(optsOf(f).method).toBe("PATCH");
  });

  it("updateMember PATCHes /members/{id}", async () => {
    const f = mockFetch({});
    await api.updateMember("m1", { status: "suspended" });
    expect(lastCall(f)[0]).toBe(`${API_BASE}/members/m1`);
    expect(optsOf(f).method).toBe("PATCH");
  });

  it("attaches a Bearer token when one is stored", async () => {
    localStorage.setItem(TOKEN_KEY, "tok123");
    const f = mockFetch({ items: [], page: {} });
    await api.listMembers();
    expect((optsOf(f).headers as Record<string, string>).Authorization).toBe("Bearer tok123");
  });

  it("throws a typed ApiError on a non-ok response", async () => {
    mockFetch({ error: { code: "conflict", message: "dup" } }, false, 409);
    await expect(api.createBook({ title: "x" })).rejects.toMatchObject({
      status: 409,
      code: "conflict",
      message: "dup",
    });
  });
});
