export default function ExternalLink({
  href,
  className,
  children,
  ...props
}: React.ComponentProps<"a">) {
  return (
    <a
      target="_blank"
      rel="noopener noreferrer"
      href={href}
      className={className}
      {...props}
    >
      {children}
    </a>
  );
}
