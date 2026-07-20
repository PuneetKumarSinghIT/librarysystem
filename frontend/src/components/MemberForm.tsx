"use client";

import { useState } from "react";
import { ApiError, Member } from "@/lib/api";
import { Errors, isValid, validateEmail, validateRequired } from "@/lib/validation";

export interface MemberPayload {
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  address: string | null;
  status?: string;
}

interface Values {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  address: string;
  status: string;
}

interface Props {
  initial?: Member;
  submitLabel: string;
  onSave: (payload: MemberPayload) => Promise<void>;
  onDone?: () => void;
  inline?: boolean;
}

export function MemberForm({ initial, submitLabel, onSave, onDone, inline }: Props) {
  const editing = Boolean(initial);
  const [v, setV] = useState<Values>({
    first_name: initial?.first_name ?? "",
    last_name: initial?.last_name ?? "",
    email: initial?.email ?? "",
    phone: initial?.phone ?? "",
    address: initial?.address ?? "",
    status: initial?.status ?? "active",
  });
  const [errors, setErrors] = useState<Errors<Values>>({});
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const set = (k: keyof Values) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => setV({ ...v, [k]: e.target.value });

  function validate(): Errors<Values> {
    return {
      first_name: validateRequired(v.first_name, "First name"),
      last_name: validateRequired(v.last_name, "Last name"),
      email: validateEmail(v.email),
    };
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setFormError("");
    const errs = validate();
    setErrors(errs);
    if (!isValid(errs)) return;

    setSubmitting(true);
    try {
      const payload: MemberPayload = {
        first_name: v.first_name.trim(),
        last_name: v.last_name.trim(),
        email: v.email.trim().toLowerCase(),
        phone: v.phone.trim() || null,
        address: v.address.trim() || null,
      };
      if (editing) payload.status = v.status;
      await onSave(payload);
      onDone?.();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Save failed");
    } finally {
      setSubmitting(false);
    }
  }

  const field = (label: string, key: keyof Values, required = false, type = "text") => {
    const id = `member-${String(key)}`;
    return (
      <div>
        <label htmlFor={id} className="mb-1 block text-sm font-medium">
          {label} {required && <span className="text-red-500">*</span>}
        </label>
        <input
          id={id}
          type={type}
          value={v[key]}
          onChange={set(key)}
          className="w-full rounded-lg border border-slate-300 px-3 py-2"
        />
        {errors[key] && <p className="mt-1 text-xs text-red-600">{errors[key]}</p>}
      </div>
    );
  };

  return (
    <form onSubmit={submit} className={inline ? "grid grid-cols-1 gap-3 sm:grid-cols-2" : "space-y-3"}>
      {field("First name", "first_name", true)}
      {field("Last name", "last_name", true)}
      {field("Email", "email", true, "email")}
      {field("Phone", "phone")}
      {editing && (
        <div>
          <label className="mb-1 block text-sm font-medium">Status</label>
          <select
            value={v.status}
            onChange={set("status")}
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
          >
            <option value="active">active</option>
            <option value="suspended">suspended</option>
          </select>
        </div>
      )}
      <div className={inline ? "sm:col-span-2" : ""}>
        {formError && <p className="mb-2 text-sm text-red-600">{formError}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-slate-900 px-4 py-2 font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? "Saving…" : submitLabel}
        </button>
      </div>
    </form>
  );
}
