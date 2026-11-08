// pins the contract of the visible-list-height hook: before any measurement it
// falls back to a fixed height, and after the first card's onLayout it fits
// exactly the requested number of cards plus gaps and box padding.
// @vitest-environment happy-dom
import { act, renderHook } from "@testing-library/react";

import type { LayoutChangeEvent } from "react-native";

import { describe, expect, it } from "vitest";

import { useVisibleListHeight } from "@/hooks/useVisibleListHeight";

function layoutEvent(height: number): LayoutChangeEvent {
  return { nativeEvent: { layout: { height } } } as LayoutChangeEvent;
}

describe("useVisibleListHeight", () => {
  it("uses the fallback height until the first card is measured", () => {
    const { result } = renderHook(() => useVisibleListHeight(6));
    expect(result.current.maxHeight).toBe(520);
  });

  it("fits exactly the requested number of cards after measuring one card", () => {
    const { result } = renderHook(() => useVisibleListHeight(6));
    act(() => result.current.onFirstCardLayout(layoutEvent(100)));
    // 6 cards + 5 gaps of 8 + 2 * 8 box padding
    expect(result.current.maxHeight).toBe(6 * 100 + 5 * 8 + 2 * 8);
  });

  it("scales with the requested card count", () => {
    const { result } = renderHook(() => useVisibleListHeight(3));
    act(() => result.current.onFirstCardLayout(layoutEvent(50)));
    expect(result.current.maxHeight).toBe(3 * 50 + 2 * 8 + 2 * 8);
  });
});
