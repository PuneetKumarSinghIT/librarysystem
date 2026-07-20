"use client";

import { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}
interface State {
  hasError: boolean;
  message: string;
}

/** Reusable client-side error boundary — catches render errors in a subtree so one
 *  broken component never blanks the whole app. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: "" };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Surface for debugging; a real app would forward this to a monitoring service.
    console.error("ErrorBoundary caught:", error, info);
  }

  reset = () => this.setState({ hasError: false, message: "" });

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback ?? (
          <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center">
            <p className="mb-2 font-medium text-red-700">Something went wrong.</p>
            <p className="mb-4 text-sm text-red-600">{this.state.message}</p>
            <button
              onClick={this.reset}
              className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-500"
            >
              Try again
            </button>
          </div>
        )
      );
    }
    return this.props.children;
  }
}
