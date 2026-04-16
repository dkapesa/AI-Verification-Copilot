export function formatDateTime(value?: string | null): string {
  if (!value) return "N/A";
  return new Date(value).toLocaleString();
}

export function formatToolName(toolName: string): string {
  return toolName
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function formatLabel(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function formatCaseId(caseId: string): string {
  if (caseId.length <= 16) return caseId;
  return `${caseId.slice(0, 8)}...${caseId.slice(-6)}`;
}

export function formatNumericValue(
  value: number | null | undefined,
  maximumFractionDigits = 2
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "N/A";
  }

  if (Number.isInteger(value)) {
    return String(value);
  }

  return value
    .toFixed(maximumFractionDigits)
    .replace(/\.?0+$/, "");
}