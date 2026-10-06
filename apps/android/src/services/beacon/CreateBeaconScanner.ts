// stands in for the real BLE scanner: simulates a steward walking past beacons, connecting
// to one, holding it for a while, losing it, then reaching the next. no Bluetooth is
// involved, so it runs in Expo Go and on the emulator; the real scanner can be dropped in
// behind the same BeaconScanner interface.
import type { BeaconConnectionEvent, BeaconEventKind } from "@/types/beacon";
import { MOCK_BEACON_IDS } from "@/fixtures/mockBeacons";
import type { BeaconScanner } from "@/types/BeaconScanner";

export function createBeaconScanner(): BeaconScanner {

  let listener: ((event: BeaconConnectionEvent) => void) | null = null;
    function emit(event: BeaconEventKind, beacon_id: string) {
      if (listener!== null) {
        listener({ event, beacon_id, timestamp: new Date().toISOString() });
      }
    }

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

