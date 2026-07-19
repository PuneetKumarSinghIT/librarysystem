"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export default function Home() {
  const { staff, ready } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!ready) return;
    router.replace(staff ? "/books" : "/login");
  }, [ready, staff, router]);

  return <p className="text-slate-500">Loading…</p>;
}
