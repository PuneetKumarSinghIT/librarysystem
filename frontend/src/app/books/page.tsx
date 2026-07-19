"use client";

import { Fragment, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, Book, Copy } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function BooksPage() {
  const { staff, ready } = useAuth();
  const router = useRouter();
  const [books, setBooks] = useState<Book[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [form, setForm] = useState({ title: "", author: "", isbn: "", category: "" });
  const [expanded, setExpanded] = useState<string | null>(null);
  const [copies, setCopies] = useState<Record<string, Copy[]>>({});
  const [barcode, setBarcode] = useState("");

  const load = useCallback(async (term = "") => {
    try {
      setError("");
      const res = await api.listBooks(term);
      setBooks(res.items);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load");
    }
  }, []);

  useEffect(() => {
    if (ready && !staff) router.replace("/login");
    else if (staff) load();
  }, [ready, staff, router, load]);

  async function createBook(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api.createBook({
        title: form.title, author: form.author,
        isbn: form.isbn || null, category: form.category || null,
      } as Partial<Book>);
      setForm({ title: "", author: "", isbn: "", category: "" });
      await load(search);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to create");
    }
  }

  async function toggleCopies(bookId: string) {
    if (expanded === bookId) { setExpanded(null); return; }
    setExpanded(bookId);
    setCopies((c) => ({ ...c, [bookId]: c[bookId] ?? [] }));
    const list = await api.listCopies(bookId);
    setCopies((c) => ({ ...c, [bookId]: list }));
  }

  async function addCopy(bookId: string) {
    if (!barcode) return;
    try {
      await api.addCopy(bookId, barcode);
      setBarcode("");
      const list = await api.listCopies(bookId);
      setCopies((c) => ({ ...c, [bookId]: list }));
      await load(search);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to add copy");
    }
  }

  if (!staff) return null;

  return (
    <div className="space-y-8">
      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold">Add a book</h2>
        <form onSubmit={createBook} className="grid grid-cols-1 gap-3 sm:grid-cols-4">
          <input placeholder="Title *" value={form.title} required
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            className="rounded-lg border border-slate-300 px-3 py-2" />
          <input placeholder="Author *" value={form.author} required
            onChange={(e) => setForm({ ...form, author: e.target.value })}
            className="rounded-lg border border-slate-300 px-3 py-2" />
          <input placeholder="ISBN" value={form.isbn}
            onChange={(e) => setForm({ ...form, isbn: e.target.value })}
            className="rounded-lg border border-slate-300 px-3 py-2" />
          <input placeholder="Category" value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
            className="rounded-lg border border-slate-300 px-3 py-2" />
          <button className="rounded-lg bg-slate-900 px-4 py-2 font-medium text-white hover:bg-slate-800 sm:col-span-4">
            Add book
          </button>
        </form>
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Catalog</h2>
          <input placeholder="Search title/author…" value={search}
            onChange={(e) => { setSearch(e.target.value); load(e.target.value); }}
            className="w-64 rounded-lg border border-slate-300 px-3 py-2" />
        </div>
        {error && <p className="mb-3 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-slate-500">
              <tr>
                <th className="px-4 py-2">Title</th><th className="px-4 py-2">Author</th>
                <th className="px-4 py-2">ISBN</th><th className="px-4 py-2">Available</th>
                <th className="px-4 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {books.map((b) => (
                <Fragment key={b.id}>
                  <tr className="border-t border-slate-100">
                    <td className="px-4 py-2 font-medium">{b.title}</td>
                    <td className="px-4 py-2">{b.author}</td>
                    <td className="px-4 py-2 text-slate-500">{b.isbn ?? "—"}</td>
                    <td className="px-4 py-2">{b.available_copies}/{b.total_copies}</td>
                    <td className="px-4 py-2 text-right">
                      <button onClick={() => toggleCopies(b.id)} className="text-slate-600 hover:underline">
                        {expanded === b.id ? "Hide" : "Copies"}
                      </button>
                    </td>
                  </tr>
                  {expanded === b.id && (
                    <tr className="bg-slate-50">
                      <td colSpan={5} className="px-4 py-3">
                        <div className="mb-2 flex gap-2">
                          <input placeholder="New barcode" value={barcode}
                            onChange={(e) => setBarcode(e.target.value)}
                            className="rounded-lg border border-slate-300 px-3 py-1.5" />
                          <button onClick={() => addCopy(b.id)}
                            className="rounded-lg bg-slate-700 px-3 py-1.5 text-white hover:bg-slate-600">
                            Add copy
                          </button>
                        </div>
                        <ul className="text-slate-600">
                          {(copies[b.id] ?? []).map((c) => (
                            <li key={c.id} className="font-mono text-xs">
                              {c.barcode} — <span className={c.status === "available" ? "text-green-600" : "text-amber-600"}>{c.status}</span>
                            </li>
                          ))}
                          {(copies[b.id]?.length ?? 0) === 0 && <li className="text-xs text-slate-400">No copies yet.</li>}
                        </ul>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
              {books.length === 0 && (
                <tr><td colSpan={5} className="px-4 py-6 text-center text-slate-400">No books.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
