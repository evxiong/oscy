import merge from "../_utils/merge";

export default function Skeleton({
  className,
  children,
}: {
  className?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className={merge("animate-pulse rounded-md bg-active", className)}>
      {children}
    </div>
  );
}
