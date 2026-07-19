"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, Book, Loan, Member } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function LoansPage() {
  const { staff, ready } = useAuth();
  const router = useRouter();
  const [members, setMembers] = useState<Member[]>([]);
  const [books, setBooks] = useState<Book[]>([]);
  const [loans, setLoans] = useState<Loan[]>([]);
  const [memberId, setMemberId] = useState("");
  const [bookId, setBookId] = useState("");
  const [activeOnly, setActiveOnly] = useState(true);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");

  const loadLoans = useCallback(async (active: boolean) => {
    const res = await api.listLoans({ active_only: active });
    setLoans(res.items);
  }, []);

  const loadAll = useCallback(async () => {
    try {
      setError("");
      const [m, b] = await Promise.all([api.listMembers(), api.listBooks()]);
      setMembers(m.items);
      setBooks(b.items);
      await loadLoans(activeOnly);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load");
    }
  }, [loadLoans, activeOnly]);

  useEffect(() => {
    if (ready && !staff) router.replace("/login");
    else if (staff) loadAll();
  }, [ready, staff, router, loadAll]);

  async function borrow(e: React.FormEvent) {
    e.preventDefault();
    setError(""); setMsg("");
    try {
      const loan = await api.borrow(memberId, undefined, bookId);
      setMsg(`Borrowed "${loan.book_title}" (${loan.barcode}) for ${loan.member_name}.`);
      await loadAll();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Borrow failed");
    }
  }

  async function returnLoan(id: string) {
    setError(""); setMsg("");
    try {
      await api.returnLoan(id);
      setMsg("Returned.");
      await loadLoans(activeOnly);
      const b = await api.listBooks();
      setBooks(b.items);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Return failed");
    }
  }

  if (!staff) return null;
  const availableBooks = books.filter((b) => b.available_copies > 0);

  return (
    <div className="space-y-8">
      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold">Borrow a book</h2>
        <form onSubmit={borrow} className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <select value={memberId} required onChange={(e) => setMemberId(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2">
            <option value="">Select member…</option>
            {members.map((m) => (
              <option key={m.id} value={m.id}>{m.first_name} {m.last_name} ({m.email})</option>
            ))}
          </select>
          <select value={bookId} required onChange={(e) => setBookId(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2">
            <option value="">Select available book…</option>
            {availableBooks.map((b) => (
              <option key={b.id} value={b.id}>{b.title} ({b.available_copies} available)</option>
            ))}
          </select>
          <button className="rounded-lg bg-slate-900 px-4 py-2 font-medium text-white hover:bg-slate-800">
            Borrow
          </button>
        </form>
        {msg && <p className="mt-3 rounded bg-green-50 px-3 py-2 text-sm text-green-700">{msg}</p>}
        {error && <p className="mt-3 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Loans</h2>
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <input type="checkbox" checked={activeOnly}
              onChange={(e) => { setActiveOnly(e.target.checked); loadLoans(e.target.checked); }} />
            Active only
          </label>
        </div>
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-slate-500">
              <tr>
                <th className="px-4 py-2">Book</th><th className="px-4 py-2">Member</th>
                <th className="px-4 py-2">Due</th><th className="px-4 py-2">Status</th>
                <th className="px-4 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {loans.map((l) => (
                <tr key={l.id} className="border-t border-slate-100">
                  <td className="px-4 py-2 font-medium">{l.book_title}<span className="ml-1 font-mono text-xs text-slate-400">{l.barcode}</span></td>
                  <td className="px-4 py-2">{l.member_name}</td>
                  <td className="px-4 py-2 text-slate-500">{new Date(l.due_at).toLocaleDateString()}</td>
                  <td className="px-4 py-2">
                    <span className={
                      l.status === "active" ? "text-green-600" :
                      l.status === "overdue" ? "text-red-600" : "text-slate-500"
                    }>{l.status}</span>
                  </td>
                  <td className="px-4 py-2 text-right">
                    {!l.returned_at && (
                      <button onClick={() => returnLoan(l.id)}
                        className="rounded border border-slate-300 px-3 py-1 hover:bg-slate-100">Return</button>
                    )}
                  </td>
                </tr>
              ))}
              {loans.length === 0 && (
                <tr><td colSpan={5} className="px-4 py-6 text-center text-slate-400">No loans.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
