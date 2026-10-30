import type { BeaconConnectionEvent } from "@/types/beacon";

/**
 * Watches for beacons around the phone and reports connect/disconnect as they
 * happen.
 *
 * The mock implementation stands in until real BLE scanning lands (it needs a
 * development build on a physical device: Expo Go and the Android emulator
 * have no Bluetooth).
 */
export type BeaconScanner = {
  /** Begin reporting events to the listener. Starting again replaces the previous listener. */
  start: (listener: (event: BeaconConnectionEvent) => void) => void;
  /** Stop scanning. No further events are reported after stop returns. */
  stop: () => void;
};
