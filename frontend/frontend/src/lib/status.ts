export function getCaseStatusBadgeClasses(status: string): string {
  switch (status) {
    case "APPROVED":
      return "border-emerald-800 bg-emerald-950/30 text-emerald-300";
    case "ESCALATED":
    case "ESCALATE":
      return "border-amber-800 bg-amber-950/30 text-amber-300";
    case "REJECTED":
    case "REJECT":
      return "border-red-800 bg-red-950/30 text-red-300";
    case "PENDING":
    default:
      return "border-slate-700 bg-slate-900 text-slate-300";
  }
}