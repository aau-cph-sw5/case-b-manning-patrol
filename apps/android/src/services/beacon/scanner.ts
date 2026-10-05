// watches for beacons around the phone and reports connect/disconnect as they happen.
// the mock implementation stands in until real BLE scanning lands (it needs a development
// build on a physical device: Expo Go and the Android emulator have no Bluetooth).
import type { BeaconEvent } from "@/types/beacon";

export type BeaconScanner = {
  // begins reporting events to the listener. starting again replaces the previous listener.
  start: (listener: (event: BeaconEvent) => void) => void;
  // stops scanning. no further events are reported after stop returns.
  stop: () => void;
};
