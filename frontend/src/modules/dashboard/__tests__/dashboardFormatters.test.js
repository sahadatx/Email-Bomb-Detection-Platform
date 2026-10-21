import { describe, expect, it } from "vitest";
import {
  formatNumber,
  metricValue,
  statusLabel,
} from "../utils/dashboardFormatters";
import { queryString } from "../services/dashboardApi";

describe("dashboard formatters", () => {
  it("formats counts and unavailable metrics without presenting missing data as zero", () => {
    expect(formatNumber(12450)).toBe("12,450");
    expect(metricValue({ value: 0, available: true })).toBe("0");
    expect(metricValue({ value: 0, available: false })).toBe("Unavailable");
  });

  it("renders status tokens as readable labels", () => {
    expect(statusLabel("never_synced")).toBe("Never Synced");
    expect(statusLabel("unknown")).toBe("Unknown");
  });

  it("omits empty filters and sends custom dates as UTC instants", () => {
    const query = new URLSearchParams(
      queryString({
        time_range: "custom",
        classification: "",
        start_date: "2026-09-01T09:30",
      }),
    );
    expect(query.get("classification")).toBeNull();
    expect(query.get("start_date")).toBe(
      new Date("2026-09-01T09:30").toISOString(),
    );
  });
});
