// pins the dev auth fixtures: the bearer token defaults to the steward role and
// the X-Android-Id header value is the mock device id.
import { describe, expect, it } from "vitest";

import { getAccessToken, getAndroidId } from "@/fixtures/auth";
import { MOCK_ANDROID_ID } from "@/fixtures/mockBeacons";

describe("auth fixtures", () => {
  it("defaults the bearer token to the steward role", async () => {
    await expect(getAccessToken()).resolves.toBe("steward");
  });

  it("returns the mock android id for the X-Android-Id header", async () => {
    await expect(getAndroidId()).resolves.toBe(MOCK_ANDROID_ID);
  });
});
