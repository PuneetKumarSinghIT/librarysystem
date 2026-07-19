"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, Member } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function MembersPage() {
  const { staff, ready } = useAuth();
  const router = useRouter();
  const [members, setMembers] = useState<Member[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [form, setForm] = useState({ first_name: "", last_name: "", email: "", phone: "" });

  const load = useCallback(async (term = "") => {
    try {
      setError("");
      const res = await api.listMembers(term);
      setMembers(res.items);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load");
    }
  }, []);

  useEffect(() => {
    if (ready && !staff) router.replace("/login");
    else if (staff) load();
  }, [ready, staff, router, load]);

  async function createMember(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api.createMember({
        first_name: form.first_name, last_name: form.last_name,
        email: form.email, phone: form.phone || null,
      } as Partial<Member>);
      setForm({ first_name: "", last_name: "", email: "", phone: "" });
      await load(search);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to create");
    }
  }

  if (!staff) return null;

  return (
    <div className="space-y-8">
      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold">Add a member</h2>
        <form onSubmit={createMember} className="grid grid-cols-1 gap-3 sm:grid-cols-4">
          <input placeholder="First name *" value={form.first_name} required
            onChange={(e) => setForm({ ...form, first_name: e.target.value })}
            className="rounded-lg border border-slate-300 px-3 py-2" />
          <input placeholder="Last name *" value={form.last_name} required
            onChange={(e) => setForm({ ...form, last_name: e.target.value })}
            className="rounded-lg border border-slate-300 px-3 py-2" />
          <input placeholder="Email *" type="email" value={form.email} required
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="rounded-lg border border-slate-300 px-3 py-2" />
          <input placeholder="Phone" value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
            className="rounded-lg border border-slate-300 px-3 py-2" />
          <button className="rounded-lg bg-slate-900 px-4 py-2 font-medium text-white hover:bg-slate-800 sm:col-span-4">
            Add member
          </button>
        </form>
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Members</h2>
          <input placeholder="Search name/email…" value={search}
            onChange={(e) => { setSearch(e.target.value); load(e.target.value); }}
            className="w-64 rounded-lg border border-slate-300 px-3 py-2" />
        </div>
        {error && <p className="mb-3 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-slate-500">
              <tr>
                <th className="px-4 py-2">Name</th><th className="px-4 py-2">Email</th>
                <th className="px-4 py-2">Phone</th><th className="px-4 py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {members.map((m) => (
                <tr key={m.id} className="border-t border-slate-100">
                  <td className="px-4 py-2 font-medium">{m.first_name} {m.last_name}</td>
                  <td className="px-4 py-2 text-slate-500">{m.email}</td>
                  <td className="px-4 py-2 text-slate-500">{m.phone ?? "—"}</td>
                  <td className="px-4 py-2">
                    <span className={m.status === "active" ? "text-green-600" : "text-amber-600"}>{m.status}</span>
                  </td>
                </tr>
              ))}
              {members.length === 0 && (
                <tr><td colSpan={4} className="px-4 py-6 text-center text-slate-400">No members.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
