"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, Member } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { PAGE_SIZE } from "@/lib/config";
import { MemberForm } from "@/components/MemberForm";
import { Column, DataTable } from "@/components/DataTable";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Modal } from "@/components/Modal";
import { Pagination } from "@/components/Pagination";

export default function MembersPage() {
  const { staff, ready } = useAuth();
  const router = useRouter();

  const [members, setMembers] = useState<Member[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<Member | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const load = useCallback(async (nextOffset: number, term: string) => {
    setLoading(true);
    setError("");
    try {
      const res = await api.listMembers({ search: term, limit: PAGE_SIZE, offset: nextOffset });
      setMembers(res.items);
      setTotal(res.page.total);
      setOffset(res.page.offset);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load members");
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
    load(0, term);
  }

  async function remove(id: string) {
    setDeletingId(id);
    setError("");
    try {
      await api.deleteMember(id);
      await load(offset, search);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to delete member");
    } finally {
      setDeletingId(null);
    }
  }

  if (!staff) return null;

  const columns: Column<Member>[] = [
    { header: "Name", cell: (m) => <span className="font-medium">{m.first_name} {m.last_name}</span> },
    { header: "Email", cell: (m) => <span className="text-slate-500">{m.email}</span> },
    { header: "Phone", cell: (m) => <span className="text-slate-500">{m.phone ?? "—"}</span> },
    {
      header: "Status",
      cell: (m) => (
        <span className={m.status === "active" ? "text-green-600" : "text-amber-600"}>{m.status}</span>
      ),
    },
    {
      header: "",
      className: "text-right",
      cell: (m) => (
        <span className="flex justify-end gap-3">
          <button onClick={() => setEditing(m)} className="text-slate-600 hover:underline">Edit</button>
          <button
            onClick={() => remove(m.id)}
            disabled={deletingId === m.id}
            className="text-red-600 hover:underline disabled:opacity-50"
          >
            {deletingId === m.id ? "Deleting…" : "Delete"}
          </button>
        </span>
      ),
    },
  ];

  return (
    <ErrorBoundary>
      <div className="space-y-8">
        <section className="rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="mb-4 text-lg font-semibold">Add a member</h2>
          <MemberForm
            submitLabel="Add member"
            inline
            onSave={async (payload) => { await api.createMember(payload); }}
            onDone={() => load(0, search)}
          />
        </section>

        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Members</h2>
            <input
              placeholder="Search name/email…"
              value={search}
              onChange={(e) => onSearch(e.target.value)}
              className="w-64 rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>
          {error && <p className="mb-3 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <DataTable columns={columns} rows={members} rowKey={(m) => m.id} loading={loading} emptyMessage="No members." />
          <Pagination limit={PAGE_SIZE} offset={offset} total={total} disabled={loading} onChange={(o) => load(o, search)} />
        </section>

        <Modal open={!!editing} title="Edit member" onClose={() => setEditing(null)}>
          {editing && (
            <MemberForm
              initial={editing}
              submitLabel="Save changes"
              onSave={async (payload) => { await api.updateMember(editing.id, payload); }}
              onDone={() => { setEditing(null); load(offset, search); }}
            />
          )}
        </Modal>
      </div>
    </ErrorBoundary>
  );
}
