"use client";

interface PaginationProps {
  limit: number;
  offset: number;
  total: number;
  onChange: (offset: number) => void;
  disabled?: boolean;
}

/** Server-side pagination controls: Prev / Next + "X–Y of Z". */
export function Pagination({ limit, offset, total, onChange, disabled }: PaginationProps) {
  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + limit, total);
  const canPrev = offset > 0 && !disabled;
  const canNext = offset + limit < total && !disabled;

  return (
    <div className="mt-3 flex items-center justify-between text-sm text-slate-600">
      <span>
        {from}–{to} of {total}
      </span>
      <div className="flex gap-2">
        <button
          onClick={() => onChange(Math.max(0, offset - limit))}
          disabled={!canPrev}
          className="rounded border border-slate-300 px-3 py-1 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-40"
        >
          ← Prev
        </button>
        <button
          onClick={() => onChange(offset + limit)}
          disabled={!canNext}
          className="rounded border border-slate-300 px-3 py-1 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Next →
        </button>
      </div>
    </div>
  );
}
