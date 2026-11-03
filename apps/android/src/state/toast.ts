/**
 * A minimal publish/subscribe store for toast messages.
 *
 * The beacon scanner fires from timer callbacks outside React, and this
 * decouples the trigger (`showToast`) from the component that renders the
 * message. The component owns the hide timer.
 */

/** Receives each message passed to {@link showToast}. */
export type ToastListener = (message: string) => void;

const listeners = new Set<ToastListener>();

/**
 * Send a message to every current subscriber.
 *
 * Safe to call from outside React. A message sent while nobody is subscribed
 * is dropped.
 */
export function showToast(message: string): void {
  for (const listener of listeners) {
    listener(message);
  }
}

/**
 * Register a listener for toast messages.
 *
 * @returns A function that unsubscribes the listener.
 */
export function subscribeToToasts(listener: ToastListener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
