import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Pagination } from "./Pagination";

describe("Pagination", () => {
  it("shows the current range and total", () => {
    render(<Pagination limit={10} offset={10} total={25} onChange={() => {}} />);
    expect(screen.getByText("11–20 of 25")).toBeInTheDocument();
  });

  it("disables Prev on the first page and Next on the last", () => {
    const { rerender } = render(<Pagination limit={10} offset={0} total={25} onChange={() => {}} />);
    expect(screen.getByRole("button", { name: /prev/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /next/i })).toBeEnabled();

    rerender(<Pagination limit={10} offset={20} total={25} onChange={() => {}} />);
    expect(screen.getByRole("button", { name: /next/i })).toBeDisabled();
  });

  it("advances the offset by the page size on Next", async () => {
    const onChange = vi.fn();
    render(<Pagination limit={10} offset={0} total={25} onChange={onChange} />);
    await userEvent.click(screen.getByRole("button", { name: /next/i }));
    expect(onChange).toHaveBeenCalledWith(10);
  });
});
