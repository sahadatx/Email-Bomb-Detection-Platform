import { describe, expect, it } from "vitest";
import { displayDate, errorMessage } from "./types";
import { queryString } from "./services/api";

describe("audit administration API helpers", () => {
  it("omits empty filters and encodes date/search values", () => {
    expect(queryString({ page: 2, search: "role update", status: "", from_date: "2026-10-01" })).toBe("?page=2&search=role+update&from_date=2026-10-01");
  });

  it("formats valid timestamps and preserves unavailable values", () => {
    expect(displayDate(null)).toBe("—");
    expect(displayDate("not-a-date")).toBe("—");
    expect(displayDate("2026-10-01T12:00:00Z")).not.toBe("Invalid Date");
  });

  it("uses readable fallback API errors", () => {
    expect(errorMessage(new Error("Request failed"))).toBe("Request failed");
    expect(errorMessage(null)).toBe("The request could not be completed.");
  });
});
