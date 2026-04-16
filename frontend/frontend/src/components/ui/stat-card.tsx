type StatCardProps = {
  label: string;
  value: string | number;
  className?: string;
  labelClassName?: string;
  valueClassName?: string;
};

function joinClasses(...values: Array<string | undefined>) {
  return values.filter(Boolean).join(" ");
}

export default function StatCard({
  label,
  value,
  className,
  labelClassName,
  valueClassName,
}: StatCardProps) {
  return (
    <div
      className={joinClasses(
        "rounded-lg border border-slate-800 bg-slate-900 p-3",
        className
      )}
    >
      <p
        className={joinClasses(
          "text-[11px] uppercase tracking-[0.18em] text-slate-500",
          labelClassName
        )}
      >
        {label}
      </p>
      <p
        className={joinClasses(
          "mt-2 text-lg font-semibold text-slate-100",
          valueClassName
        )}
      >
        {value}
      </p>
    </div>
  );
}