import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BookForm } from "./BookForm";

describe("BookForm", () => {
  it("shows validation errors and does not submit when required fields are blank", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(<BookForm submitLabel="Add book" onSave={onSave} />);

    await userEvent.click(screen.getByRole("button", { name: /add book/i }));

    expect(await screen.findByText("Title is required")).toBeInTheDocument();
    expect(screen.getByText("Author is required")).toBeInTheDocument();
    expect(onSave).not.toHaveBeenCalled();
  });

  it("rejects whitespace-only input (not just empty)", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(<BookForm submitLabel="Add book" onSave={onSave} />);

    await userEvent.type(screen.getByLabelText(/title/i), "   ");
    await userEvent.type(screen.getByLabelText(/author/i), "   ");
    await userEvent.click(screen.getByRole("button", { name: /add book/i }));

    expect(await screen.findByText("Title is required")).toBeInTheDocument();
    expect(onSave).not.toHaveBeenCalled();
  });

  it("trims values and submits a cleaned payload", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    const onDone = vi.fn();
    render(<BookForm submitLabel="Add book" onSave={onSave} onDone={onDone} />);

    await userEvent.type(screen.getByLabelText(/title/i), "  Clean Code  ");
    await userEvent.type(screen.getByLabelText(/author/i), " Robert Martin ");
    await userEvent.click(screen.getByRole("button", { name: /add book/i }));

    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    expect(onSave).toHaveBeenCalledWith(
      expect.objectContaining({ title: "Clean Code", author: "Robert Martin" }),
    );
    expect(onDone).toHaveBeenCalled();
  });

  it("disables the submit button while the request is in flight", async () => {
    let resolve!: () => void;
    const onSave = vi.fn().mockReturnValue(new Promise<void>((r) => (resolve = r)));
    render(<BookForm submitLabel="Add book" onSave={onSave} />);

    await userEvent.type(screen.getByLabelText(/title/i), "T");
    await userEvent.type(screen.getByLabelText(/author/i), "A");
    await userEvent.click(screen.getByRole("button", { name: /add book/i }));

    // While the promise is pending the button is disabled and shows "Saving…"
    const btn = await screen.findByRole("button", { name: /saving/i });
    expect(btn).toBeDisabled();

    resolve();
    await waitFor(() => expect(screen.getByRole("button", { name: /add book/i })).toBeEnabled());
  });
});
