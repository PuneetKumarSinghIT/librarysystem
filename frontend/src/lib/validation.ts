// Reusable client-side form validation.
// Trims input, rejects empty / whitespace-only values, and enforces field formats
// so we never submit blank or malformed data (defense in depth with the server).

export type Errors<T> = Partial<Record<keyof T, string>>;

export const isBlank = (v: string | null | undefined): boolean =>
  !v || v.trim().length === 0;

/** Trim every string field of an object (returns a new object). */
export function trimAll<T extends Record<string, unknown>>(obj: T): T {
  const out = { ...obj };
  for (const key of Object.keys(out) as (keyof T)[]) {
    const val = out[key];
    if (typeof val === "string") out[key] = val.trim() as T[keyof T];
  }
  return out;
}

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export function validateEmail(value: string): string | undefined {
  if (isBlank(value)) return "Email is required";
  if (!EMAIL_RE.test(value.trim())) return "Enter a valid email address";
  return undefined;
}

export function validateRequired(value: string, label: string): string | undefined {
  if (isBlank(value)) return `${label} is required`;
  return undefined;
}

/** ISBN is optional; when present it must be a valid ISBN-10 or ISBN-13. */
export function validateIsbn(value: string): string | undefined {
  const cleaned = value.trim().replace(/[-\s]/g, "");
  if (cleaned.length === 0) return undefined;
  if (![10, 13].includes(cleaned.length) || !/^\d+[\dXx]?$/.test(cleaned)) {
    return "ISBN must be a valid ISBN-10 or ISBN-13";
  }
  return undefined;
}

/** Year is optional; when present it must be within a sensible range. */
export function validateYear(value: string): string | undefined {
  const trimmed = value.trim();
  if (trimmed.length === 0) return undefined;
  const year = Number(trimmed);
  const nextYear = new Date().getFullYear() + 1;
  if (!Number.isInteger(year) || year < 1400 || year > nextYear) {
    return `Year must be between 1400 and ${nextYear}`;
  }
  return undefined;
}

/** True when an errors object has no messages. */
export const isValid = <T,>(errors: Errors<T>): boolean =>
  Object.values(errors).every((e) => !e);
