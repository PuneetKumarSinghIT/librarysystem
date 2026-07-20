"use client";

import { useState } from "react";
import { ApiError, Book } from "@/lib/api";
import {
  Errors,
  isValid,
  validateIsbn,
  validateRequired,
  validateYear,
} from "@/lib/validation";

export interface BookPayload {
  title: string;
  author: string;
  isbn: string | null;
  category: string | null;
  published_year: number | null;
}

interface Values {
  title: string;
  author: string;
  isbn: string;
  category: string;
  published_year: string;
}

interface Props {
  initial?: Book;
  submitLabel: string;
  onSave: (payload: BookPayload) => Promise<void>;
  onDone?: () => void;
  inline?: boolean; // inline (create) vs modal (edit) layout
}

export function BookForm({ initial, submitLabel, onSave, onDone, inline }: Props) {
  const [v, setV] = useState<Values>({
    title: initial?.title ?? "",
    author: initial?.author ?? "",
    isbn: initial?.isbn ?? "",
    category: initial?.category ?? "",
    published_year: initial?.published_year ? String(initial.published_year) : "",
  });
  const [errors, setErrors] = useState<Errors<Values>>({});
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const set = (k: keyof Values) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setV({ ...v, [k]: e.target.value });

  function validate(): Errors<Values> {
    return {
      title: validateRequired(v.title, "Title"),
      author: validateRequired(v.author, "Author"),
      isbn: validateIsbn(v.isbn),
      published_year: validateYear(v.published_year),
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
      await onSave({
        title: v.title.trim(),
        author: v.author.trim(),
        isbn: v.isbn.trim() || null,
        category: v.category.trim() || null,
        published_year: v.published_year.trim() ? Number(v.published_year.trim()) : null,
      });
      onDone?.();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Save failed");
    } finally {
      setSubmitting(false);
    }
  }

  const field = (
    label: string,
    key: keyof Values,
    opts: { required?: boolean; type?: string } = {},
  ) => {
    const id = `book-${String(key)}`;
    return (
      <div>
        <label htmlFor={id} className="mb-1 block text-sm font-medium">
          {label} {opts.required && <span className="text-red-500">*</span>}
        </label>
        <input
          id={id}
          type={opts.type ?? "text"}
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
      {field("Title", "title", { required: true })}
      {field("Author", "author", { required: true })}
      {field("ISBN", "isbn")}
      {field("Category", "category")}
      {field("Published year", "published_year")}
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
