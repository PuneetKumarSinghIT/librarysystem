"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";

const LINKS = [
  { href: "/books", label: "Books" },
  { href: "/members", label: "Members" },
  { href: "/loans", label: "Lending" },
];

export function Nav() {
  const { staff, logout } = useAuth();
  const pathname = usePathname();
  if (pathname === "/login" || !staff) return null;

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-6">
          <span className="text-lg font-semibold">📚 Neighborhood Library</span>
          <nav className="flex gap-1">
            {LINKS.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className={`rounded px-3 py-1.5 text-sm font-medium ${
                  pathname === l.href
                    ? "bg-slate-900 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                {l.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <span className="text-slate-500">{staff.email} ({staff.role})</span>
          <button onClick={logout} className="rounded border border-slate-300 px-3 py-1.5 hover:bg-slate-100">
            Log out
          </button>
        </div>
      </div>
    </header>
  );
}
