import { Wordmark } from "@/components/wordmark";

/**
 * Shown until the stored session has been read. Standing in for the real
 * screen keeps a signed-in user from seeing the auth form flash by, and gives
 * the prerendered page something to paint before hydration.
 */
export default function Splash() {
  return (
    <div className="fixed inset-0 flex items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <Wordmark />
        <span className="animate-glow text-[10px] tracking-[2px] text-muted">
          connecting
        </span>
      </div>
    </div>
  );
}
