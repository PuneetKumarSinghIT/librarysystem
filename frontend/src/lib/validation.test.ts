import { describe, expect, it } from "vitest";
import {
  isBlank,
  isValid,
  trimAll,
  validateEmail,
  validateIsbn,
  validateRequired,
  validateYear,
} from "./validation";

describe("isBlank", () => {
  it("treats empty and whitespace-only as blank", () => {
    expect(isBlank("")).toBe(true);
    expect(isBlank("   ")).toBe(true);
    expect(isBlank(null)).toBe(true);
    expect(isBlank(undefined)).toBe(true);
    expect(isBlank("x")).toBe(false);
  });
});

describe("trimAll", () => {
  it("trims all string fields", () => {
    expect(trimAll({ a: "  hi ", b: 3, c: "x " })).toEqual({ a: "hi", b: 3, c: "x" });
  });
});

describe("validateRequired", () => {
  it("rejects blank / whitespace-only", () => {
    expect(validateRequired("  ", "Title")).toBe("Title is required");
    expect(validateRequired("ok", "Title")).toBeUndefined();
  });
});

describe("validateEmail", () => {
  it("requires a value and a valid format", () => {
    expect(validateEmail("")).toBe("Email is required");
    expect(validateEmail("not-an-email")).toBe("Enter a valid email address");
    expect(validateEmail("a@b.com")).toBeUndefined();
    expect(validateEmail("  a@b.com ")).toBeUndefined(); // trims
  });
});

describe("validateIsbn", () => {
  it("is optional but validates length when present", () => {
    expect(validateIsbn("")).toBeUndefined();
    expect(validateIsbn("123")).toContain("ISBN");
    expect(validateIsbn("978-0-13-235088-4")).toBeUndefined(); // ISBN-13 w/ hyphens
    expect(validateIsbn("0132350882")).toBeUndefined(); // ISBN-10
  });
});

describe("validateYear", () => {
  it("is optional but bounded when present", () => {
    expect(validateYear("")).toBeUndefined();
    expect(validateYear("999")).toContain("Year");
    expect(validateYear("2020")).toBeUndefined();
    const future = String(new Date().getFullYear() + 5);
    expect(validateYear(future)).toContain("Year");
  });
});

describe("isValid", () => {
  it("is true only when no messages exist", () => {
    expect(isValid({ a: undefined, b: undefined })).toBe(true);
    expect(isValid({ a: "err" })).toBe(false);
  });
});
