/**
 * Placeholder for the real BLE beacon scanner.
 *
 * Real scanning needs a development build on a physical device (Expo Go and
 * the Android emulator have no Bluetooth). Until it is written, the app uses
 * `createMockBeaconScanner` behind the same {@link BeaconScanner} interface.
 */
import type { BeaconConnectionEvent } from "@/types/beacon";
import type { BeaconScanner } from "@/types/BeaconScanner";

/** Create the real beacon scanner. Not implemented yet: `start` and `stop` both throw. */
export function createBeaconScanner(): BeaconScanner {
  // commented out for now, since we don't have a real scanner yet. when we do, we'll just drop it in behind the same interface.
  // let listener: ((event: BeaconConnectionEvent) => void) | null = null;
  // function emit(event: BeaconEventKind, beacon_id: string) {
  //   if (listener !== null) {
  //     listener({ event, beacon_id, timestamp: new Date().toISOString() });
  //   }
  // }

    function startFunction(l: (event: BeaconConnectionEvent) => void) {
        // bluetooth logic:
        // emit("CONNECTED", "some id");
        throw new Error("Not implemented yet.")
    }

    function stopFunction(): void {
      // stop searching...
      throw new Error("Not implemented yet.")
    }

    const scanner: BeaconScanner = {
        start: startFunction,
        stop: stopFunction
    };
    return scanner;
}
