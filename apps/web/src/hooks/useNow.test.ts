// @vitest-environment jsdom
import { act, cleanup, renderHook } from '@testing-library/react'

import { afterEach, describe, expect, it, vi } from 'vitest'

import { resolveFakeNow, useNow } from './useNow'

const FAKE = '2026-11-01T23:50:00Z'

afterEach(() => {
  cleanup()
  vi.useRealTimers()
  window.history.replaceState({}, '', '/')
})

describe('resolveFakeNow', () => {
  it('parses an ISO timestamp', () => {
    expect(resolveFakeNow(`?fakeNow=${FAKE}`, true)).toBe(Date.parse(FAKE))
  })

  it('parses epoch milliseconds', () => {
    expect(resolveFakeNow('?fakeNow=1772000000000', true)).toBe(1772000000000)
  })

  it('returns null without the param', () => {
    expect(resolveFakeNow('', true)).toBeNull()
    expect(resolveFakeNow('?other=1', true)).toBeNull()
  })

  it('returns null for an invalid value', () => {
    expect(resolveFakeNow('?fakeNow=banana', true)).toBeNull()
  })

  it('is disabled outside dev mode', () => {
    expect(resolveFakeNow(`?fakeNow=${FAKE}`, false)).toBeNull()
  })
})

describe('useNow', () => {
  it('uses the real clock by default and ticks every second', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-11-02T11:42:00Z'))
    const { result } = renderHook(() => useNow())
    expect(result.current).toBe(Date.parse('2026-11-02T11:42:00Z'))
    act(() => {
      vi.advanceTimersByTime(1000)
    })
    expect(result.current).toBe(Date.parse('2026-11-02T11:42:01Z'))
  })

  it('runs on the fake clock from ?fakeNow= and keeps ticking from it', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-11-02T11:42:00Z'))
    window.history.replaceState({}, '', `/?fakeNow=${FAKE}`)
    const { result } = renderHook(() => useNow())
    expect(result.current).toBe(Date.parse(FAKE))
    act(() => {
      vi.advanceTimersByTime(60_000)
    })
    expect(result.current).toBe(Date.parse(FAKE) + 60_000)
  })
})
