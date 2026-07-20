"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, Book, Loan, Member } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { PAGE_SIZE } from "@/lib/config";
import { Column, DataTable } from "@/components/DataTable";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Pagination } from "@/components/Pagination";

const DROPDOWN_LIMIT = 100;

export default function LoansPage() {
  const { staff, ready } = useAuth();
  const router = useRouter();

  const [members, setMembers] = useState<Member[]>([]);
  const [books, setBooks] = useState<Book[]>([]);
  const [loans, setLoans] = useState<Loan[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [activeOnly, setActiveOnly] = useState(true);
  const [loading, setLoading] = useState(true);

  const [memberId, setMemberId] = useState("");
  const [bookId, setBookId] = useState("");
  const [borrowing, setBorrowing] = useState(false);
  const [returningId, setReturningId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");

  const loadLoans = useCallback(async (nextOffset: number, active: boolean) => {
    setLoading(true);
    try {
      const res = await api.listLoans({ active_only: active, limit: PAGE_SIZE, offset: nextOffset });
      setLoans(res.items);
      setTotal(res.page.total);
      setOffset(res.page.offset);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load loans");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadDropdowns = useCallback(async () => {
    const [m, b] = await Promise.all([
      api.listMembers({ limit: DROPDOWN_LIMIT }),
      api.listBooks({ limit: DROPDOWN_LIMIT }),
    ]);
    setMembers(m.items);
    setBooks(b.items);
  }, []);

  useEffect(() => {
    if (ready && !staff) { router.replace("/login"); return; }
    if (staff) {
      loadDropdowns().catch(() => setError("Failed to load form data"));
      loadLoans(0, activeOnly); // initial load; the toggle handler reloads on change
    }
    // activeOnly intentionally excluded: the toggle handler drives subsequent reloads.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, staff, router, loadDropdowns, loadLoans]);

  async function borrow(e: React.FormEvent) {
    e.preventDefault();
    setError(""); setMsg("");
    if (!memberId || !bookId) { setError("Select a member and a book"); return; }
    setBorrowing(true);
    try {
      const loan = await api.borrow(memberId, undefined, bookId);
      setMsg(`Borrowed "${loan.book_title}" (${loan.barcode}) for ${loan.member_name}.`);
      setBookId("");
      await Promise.all([loadDropdowns(), loadLoans(offset, activeOnly)]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Borrow failed");
    } finally {
      setBorrowing(false);
    }
  }

  async function returnLoan(id: string) {
    setError(""); setMsg("");
    setReturningId(id);
    try {
      await api.returnLoan(id);
      setMsg("Returned.");
      await Promise.all([loadDropdowns(), loadLoans(offset, activeOnly)]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Return failed");
    } finally {
      setReturningId(null);
    }
  }

  if (!staff) return null;
  const availableBooks = books.filter((b) => b.available_copies > 0);

  const columns: Column<Loan>[] = [
    {
      header: "Book",
      cell: (l) => (
        <span className="font-medium">
          {l.book_title}
          <span className="ml-1 font-mono text-xs text-slate-400">{l.barcode}</span>
        </span>
      ),
    },
    { header: "Member", cell: (l) => l.member_name },
    { header: "Due", cell: (l) => <span className="text-slate-500">{new Date(l.due_at).toLocaleDateString()}</span> },
    {
      header: "Status",
      cell: (l) => (
        <span className={
          l.status === "active" ? "text-green-600" : l.status === "overdue" ? "text-red-600" : "text-slate-500"
        }>{l.status}</span>
      ),
    },
    {
      header: "",
      className: "text-right",
      cell: (l) =>
        !l.returned_at ? (
          <button
            onClick={() => returnLoan(l.id)}
            disabled={returningId === l.id}
            className="rounded border border-slate-300 px-3 py-1 hover:bg-slate-100 disabled:opacity-50"
          >
            {returningId === l.id ? "Returning…" : "Return"}
          </button>
        ) : null,
    },
  ];

  return (
    <ErrorBoundary>
      <div className="space-y-8">
        <section className="rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="mb-4 text-lg font-semibold">Borrow a book</h2>
          <form onSubmit={borrow} className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <select value={memberId} onChange={(e) => setMemberId(e.target.value)} className="rounded-lg border border-slate-300 px-3 py-2">
              <option value="">Select member…</option>
              {members.map((m) => (
                <option key={m.id} value={m.id}>{m.first_name} {m.last_name} ({m.email})</option>
              ))}
            </select>
            <select value={bookId} onChange={(e) => setBookId(e.target.value)} className="rounded-lg border border-slate-300 px-3 py-2">
              <option value="">Select available book…</option>
              {availableBooks.map((b) => (
                <option key={b.id} value={b.id}>{b.title} ({b.available_copies} available)</option>
              ))}
            </select>
            <button
              type="submit"
              disabled={borrowing}
              className="rounded-lg bg-slate-900 px-4 py-2 font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {borrowing ? "Borrowing…" : "Borrow"}
            </button>
          </form>
          {msg && <p className="mt-3 rounded bg-green-50 px-3 py-2 text-sm text-green-700">{msg}</p>}
          {error && <p className="mt-3 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        </section>

        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Loans</h2>
            <label className="flex items-center gap-2 text-sm text-slate-600">
              <input
                type="checkbox"
                checked={activeOnly}
                onChange={(e) => { setActiveOnly(e.target.checked); loadLoans(0, e.target.checked); }}
              />
              Active only
            </label>
          </div>
          <DataTable columns={columns} rows={loans} rowKey={(l) => l.id} loading={loading} emptyMessage="No loans." />
          <Pagination limit={PAGE_SIZE} offset={offset} total={total} disabled={loading} onChange={(o) => loadLoans(o, activeOnly)} />
        </section>
      </div>
    </ErrorBoundary>
  );
}
