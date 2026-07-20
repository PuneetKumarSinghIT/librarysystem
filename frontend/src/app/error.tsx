"use client";

// Next.js App Router route-level error boundary — catches errors thrown while
// rendering any page under app/, and offers a recovery action.

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="mx-auto mt-16 max-w-md rounded-xl border border-red-200 bg-red-50 p-8 text-center">
      <h2 className="mb-2 text-xl font-semibold text-red-700">Something went wrong</h2>
      <p className="mb-6 text-sm text-red-600">{error.message || "An unexpected error occurred."}</p>
      <button
        onClick={reset}
        className="rounded-lg bg-red-600 px-4 py-2 font-medium text-white hover:bg-red-500"
      >
        Try again
      </button>
    </div>
  );
}
