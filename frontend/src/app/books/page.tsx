"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, Book, Copy } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { PAGE_SIZE } from "@/lib/config";
import { isBlank } from "@/lib/validation";
import { BookForm } from "@/components/BookForm";
import { Column, DataTable } from "@/components/DataTable";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Modal } from "@/components/Modal";
import { Pagination } from "@/components/Pagination";

export default function BooksPage() {
  const { staff, ready } = useAuth();
  const router = useRouter();

  const [books, setBooks] = useState<Book[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [editing, setEditing] = useState<Book | null>(null);
  const [copiesFor, setCopiesFor] = useState<Book | null>(null);

  const load = useCallback(async (nextOffset: number, term: string) => {
    setLoading(true);
    setError("");
    try {
      const res = await api.listBooks({ search: term, limit: PAGE_SIZE, offset: nextOffset });
      setBooks(res.items);
      setTotal(res.page.total);
      setOffset(res.page.offset);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load books");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (ready && !staff) router.replace("/login");
    else if (staff) load(0, "");
  }, [ready, staff, router, load]);

  function onSearch(term: string) {
    setSearch(term);
    load(0, term); // server-side search resets to first page
  }

  if (!staff) return null;

  const columns: Column<Book>[] = [
    { header: "Title", cell: (b) => <span className="font-medium">{b.title}</span> },
    { header: "Author", cell: (b) => b.author },
    { header: "ISBN", cell: (b) => <span className="text-slate-500">{b.isbn ?? "—"}</span> },
    { header: "Available", cell: (b) => `${b.available_copies}/${b.total_copies}` },
    {
      header: "",
      className: "text-right",
      cell: (b) => (
        <span className="flex justify-end gap-3">
          <button onClick={() => setEditing(b)} className="text-slate-600 hover:underline">Edit</button>
          <button onClick={() => setCopiesFor(b)} className="text-slate-600 hover:underline">Copies</button>
        </span>
      ),
    },
  ];

  return (
    <ErrorBoundary>
      <div className="space-y-8">
        <section className="rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="mb-4 text-lg font-semibold">Add a book</h2>
          <BookForm
            submitLabel="Add book"
            inline
            onSave={async (payload) => { await api.createBook(payload); }}
            onDone={() => load(0, search)}
          />
        </section>

        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Catalog</h2>
            <input
              placeholder="Search title/author…"
              value={search}
              onChange={(e) => onSearch(e.target.value)}
              className="w-64 rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>
          {error && <p className="mb-3 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <DataTable columns={columns} rows={books} rowKey={(b) => b.id} loading={loading} emptyMessage="No books." />
          <Pagination limit={PAGE_SIZE} offset={offset} total={total} disabled={loading} onChange={(o) => load(o, search)} />
        </section>

        {/* Edit book modal */}
        <Modal open={!!editing} title="Edit book" onClose={() => setEditing(null)}>
          {editing && (
            <BookForm
              initial={editing}
              submitLabel="Save changes"
              onSave={async (payload) => { await api.updateBook(editing.id, payload); }}
              onDone={() => { setEditing(null); load(offset, search); }}
            />
          )}
        </Modal>

        {/* Manage copies modal */}
        <Modal open={!!copiesFor} title={`Copies — ${copiesFor?.title ?? ""}`} onClose={() => setCopiesFor(null)}>
          {copiesFor && (
            <CopiesPanel book={copiesFor} onChanged={() => load(offset, search)} />
          )}
        </Modal>
      </div>
    </ErrorBoundary>
  );
}

function CopiesPanel({ book, onChanged }: { book: Book; onChanged: () => void }) {
  const [copies, setCopies] = useState<Copy[]>([]);
  const [loading, setLoading] = useState(true);
  const [barcode, setBarcode] = useState("");
  const [fieldError, setFieldError] = useState("");
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setCopies(await api.listCopies(book.id));
    } finally {
      setLoading(false);
    }
  }, [book.id]);

  useEffect(() => { load(); }, [load]);

  async function addCopy(e: React.FormEvent) {
    e.preventDefault();
    setFormError("");
    if (isBlank(barcode)) { setFieldError("Barcode is required"); return; }
    setFieldError("");
    setSubmitting(true);
    try {
      await api.addCopy(book.id, barcode.trim());
      setBarcode("");
      await load();
      onChanged();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Failed to add copy");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <form onSubmit={addCopy} className="mb-3 flex gap-2">
        <input
          placeholder="New barcode"
          value={barcode}
          onChange={(e) => setBarcode(e.target.value)}
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2"
        />
        <button
          type="submit"
          disabled={submitting}
          className="rounded-lg bg-slate-700 px-3 py-2 text-white hover:bg-slate-600 disabled:opacity-50"
        >
          {submitting ? "Adding…" : "Add"}
        </button>
      </form>
      {fieldError && <p className="mb-2 text-xs text-red-600">{fieldError}</p>}
      {formError && <p className="mb-2 text-sm text-red-600">{formError}</p>}
      {loading ? (
        <p className="text-sm text-slate-400">Loading copies…</p>
      ) : (
        <ul className="max-h-52 space-y-1 overflow-y-auto">
          {copies.map((c) => (
            <li key={c.id} className="font-mono text-xs">
              {c.barcode} —{" "}
              <span className={c.status === "available" ? "text-green-600" : "text-amber-600"}>{c.status}</span>
            </li>
          ))}
          {copies.length === 0 && <li className="text-xs text-slate-400">No copies yet.</li>}
        </ul>
      )}
    </div>
  );
}
