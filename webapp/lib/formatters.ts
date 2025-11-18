/**
 * Number formatting utilities for better UX
 */

export function formatCurrency(value: number | string | undefined | null): string {
  if (value === undefined || value === null || value === "") return "";
  const num = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(num)) return "";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(num);
}

export function formatNumber(value: number | string | undefined | null): string {
  if (value === undefined || value === null || value === "") return "";
  const num = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(num)) return "";
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(num);
}

export function formatPercentage(value: number | string | undefined | null, asDecimal = false): string {
  if (value === undefined || value === null || value === "") return "";
  const num = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(num)) return "";
  const percentage = asDecimal ? num * 100 : num;
  return `${percentage.toFixed(2)}%`;
}

export function parseFormattedNumber(value: string): number {
  // Remove commas and other formatting
  const cleaned = value.replace(/[,$%]/g, "");
  const parsed = parseFloat(cleaned);
  return isNaN(parsed) ? 0 : parsed;
}

export function decimalToPercentage(decimal: number): number {
  // Round to 2 decimal places to avoid floating point precision issues (e.g., 0.07 * 100 = 7.000000001)
  return Math.round(decimal * 10000) / 100;
}

export function percentageToDecimal(percentage: number): number {
  return percentage / 100;
}

