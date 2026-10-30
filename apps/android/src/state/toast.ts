/** Receives each toast message as it is shown. */
export type ToastListener = (message: string) => void;

const listeners = new Set<ToastListener>();

/**
 * Send a message to every current toast subscriber.
 *
 * Part of a minimal publish/subscribe store. The beacon scanner fires from
 * timer callbacks outside React, and this decouples the trigger from the
 * component that renders the message; the component owns the hide timer.
 * With no subscriber mounted, the message is dropped.
 */
export function showToast(message: string): void {
  for (const listener of listeners) {
    listener(message);
  }
}

/**
 * Register a listener for toast messages.
 *
 * @returns A function that removes the listener again.
 */
export function subscribeToToasts(listener: ToastListener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
