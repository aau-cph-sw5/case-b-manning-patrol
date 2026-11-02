// a minimal publish/subscribe store for toast messages. the beacon scanner fires
// from timer callbacks outside React, and this decouples the trigger (showToast)
// from the component that renders the message. the component owns the hide timer.
export type ToastListener = (message: string) => void;

const listeners = new Set<ToastListener>();

export function showToast(message: string): void {
  for (const listener of listeners) {
    listener(message);
  }
}

export function subscribeToToasts(listener: ToastListener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
