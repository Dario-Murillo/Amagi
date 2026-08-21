export function Wordmark({ size = "lg" }: { size?: "lg" | "sm" }) {
  return (
    <span
      className={
        size === "lg"
          ? "font-display text-[32px] leading-none tracking-[3px] text-accent"
          : "font-display text-xl leading-none tracking-[2px] text-accent"
      }
    >
      AMAGI
    </span>
  );
}
