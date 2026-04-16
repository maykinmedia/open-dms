import { useEffect, useRef } from "react";

export type UsePollOptions = {
  /** Time between completion of the previous and start of the next tick. */
  timeout?: number;

  /** Function to call when tick fails. */
  onError?: (e: unknown) => void;
};

/**
 * Polls `fn` every [`options.timeout=30000`]ms.
 * Reschedules after `fn` resolution to prevent flooding.
 * @param fn - Receives an AbortSignal which gets called on cleanup.
 * @param options - Options
 * @param deps - React deps
 */
export function usePoll<T = unknown>(
  fn: (signal: AbortSignal) => T | Promise<T>,
  deps?: unknown[],
  options?: {
    timeout?: number;
    onError?: (e: unknown) => void;
  },
) {
  const active = useRef(true);
  const ref = useRef(-1);

  const cancel = () => {
    active.current = false;
    window.clearTimeout(ref.current);
  };

  useEffect(() => {
    const controller = new AbortController();
    /** Performs single "tick", awaits`fn()`, then calls `poll()` to reschedule. */
    const tick = async () => {
      try {
        // Call fn().
        await fn(controller.signal);
      } catch (e) {
        options?.onError?.(e);
      } finally {
        // Reschedule next tick.
        poll();
      }
    };

    /** Sets a timeout of `[options.timeout=3000]` to schedule `tick()`. */
    const poll = () => {
      // Stop.
      if (active.current) {
        ref.current = window.setTimeout(() => tick(), options?.timeout ?? 3000);
      }
    };

    // Schedule first run.
    tick();

    // Return a function that clears the scheduled `tick()`.
    return () => {
      controller.abort();
      cancel();
    };
  }, deps);

  useEffect(() => {
    active.current = true;
  });

  // Return a function that clears the scheduled `tick()`.
  return cancel;
}
