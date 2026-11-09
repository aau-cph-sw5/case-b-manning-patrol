/** Hook that sizes a list box to show a fixed number of cards. */

import { useState } from "react";

import type { LayoutChangeEvent } from "react-native";

/** Gap between cards inside a list box. */
const LIST_GAP = 8;
/** Vertical padding of a list box. */
const BOX_PADDING = 8;
/** Box height used until the first card has been measured. */
const FALLBACK_HEIGHT = 520;

export type VisibleListHeight = {
  /** Max height for the box: fits the requested number of cards, gaps and padding. */
  maxHeight: number;
  /** Attach to the first card's onLayout to measure the card height. */
  onFirstCardLayout: (event: LayoutChangeEvent) => void;
};

/**
 * Return the max box height that shows exactly `visibleCards` cards, plus an
 * onLayout handler for the first card.
 *
 * Until the first card reports its height the fallback height is used; after
 * that the height is `visibleCards` card heights plus the gaps between them
 * and the box padding, so the box stays the same size no matter how many
 * records it contains.
 */
export function useVisibleListHeight(visibleCards: number): VisibleListHeight {
  const [cardHeight, setCardHeight] = useState(0);

  const maxHeight =
    cardHeight > 0
      ? visibleCards * cardHeight + (visibleCards - 1) * LIST_GAP + 2 * BOX_PADDING
      : FALLBACK_HEIGHT;

  return {
    maxHeight,
    onFirstCardLayout: (event) => setCardHeight(event.nativeEvent.layout.height),
  };
}
