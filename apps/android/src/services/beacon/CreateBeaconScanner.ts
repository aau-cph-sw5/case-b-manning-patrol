import type { BeaconConnectionEvent } from "@/types/beacon";
import type { BeaconScanner } from "@/types/BeaconScanner";

/**
 * Create the real BLE beacon scanner. Not implemented yet.
 *
 * Placeholder behind the {@link BeaconScanner} interface: both `start` and
 * `stop` throw "Not implemented yet.". Nothing calls it yet; the app uses
 * `createMockBeaconScanner` instead.
 */
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
      throw new Error("Not implemented yet.")
    }

    const scanner: BeaconScanner = {
        start: startFunction,
        stop: stopFunction
    };
    return scanner;
}
