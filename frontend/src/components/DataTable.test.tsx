import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { Column, DataTable } from "./DataTable";

interface Row { id: string; name: string }
const columns: Column<Row>[] = [{ header: "Name", cell: (r) => r.name }];

describe("DataTable", () => {
  it("shows a loading state", () => {
    render(<DataTable columns={columns} rows={[]} rowKey={(r) => r.id} loading emptyMessage="none" />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("shows the empty message when there are no rows", () => {
    render(<DataTable columns={columns} rows={[]} rowKey={(r) => r.id} emptyMessage="No rows here" />);
    expect(screen.getByText("No rows here")).toBeInTheDocument();
  });

  it("renders one row per item", () => {
    const rows: Row[] = [{ id: "1", name: "Ada" }, { id: "2", name: "Alan" }];
    render(<DataTable columns={columns} rows={rows} rowKey={(r) => r.id} />);
    expect(screen.getByText("Ada")).toBeInTheDocument();
    expect(screen.getByText("Alan")).toBeInTheDocument();
  });
});
