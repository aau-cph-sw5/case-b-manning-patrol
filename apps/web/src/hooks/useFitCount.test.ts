// @vitest-environment jsdom
import { act, cleanup, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useFitCount } from './useFitCount'

// jsdom has no ResizeObserver
class FakeResizeObserver {
  static last: FakeResizeObserver | undefined
  callback: () => void
  observe = vi.fn()
  disconnect = vi.fn()

  constructor(callback: () => void) {
    this.callback = callback
    FakeResizeObserver.last = this
  }
}

// Element heights have to be set by hand
function setHeight(
  el: HTMLElement,
  prop: 'clientHeight' | 'offsetHeight',
  px: number,
) {
  Object.defineProperty(el, prop, { configurable: true, value: px })
}

function addRow(list: HTMLElement, height: number) {
  const row = document.createElement('li')
  setHeight(row, 'offsetHeight', height)
  list.append(row)
}

function makeList(listHeight: number, rowHeight?: number) {
  const list = document.createElement('ul')
  setHeight(list, 'clientHeight', listHeight)
  if (rowHeight !== undefined) addRow(list, rowHeight)
  return list
}

beforeEach(() => {
  vi.stubGlobal('ResizeObserver', FakeResizeObserver)
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  FakeResizeObserver.last = undefined
})

describe('useFitCount', () => {
  it('counts how many whole rows fit in the list', () => {
    const { result } = renderHook(() =>
      useFitCount({ current: makeList(100, 30) }),
    )
    expect(result.current).toBe(3)
  })

  it('always fits at least one row', () => {
    const { result } = renderHook(() =>
      useFitCount({ current: makeList(10, 30) }),
    )
    expect(result.current).toBe(1)
  })

  it('fits everything while the list is empty', () => {
    const { result } = renderHook(() => useFitCount({ current: makeList(100) }))
    expect(result.current).toBe(Infinity)
  })

  it('does nothing before the list is mounted', () => {
    const { result } = renderHook(() => useFitCount({ current: null }))
    expect(result.current).toBe(Infinity)
    expect(FakeResizeObserver.last).toBeUndefined()
  })

  it('measures once rows appear after the first render', () => {
    const list = makeList(100)
    const { result, rerender } = renderHook(() =>
      useFitCount({ current: list }),
    )
    expect(result.current).toBe(Infinity)

    addRow(list, 25)
    rerender()
    expect(result.current).toBe(4)
  })

  it('measures again when the list is resized', () => {
    const list = makeList(100, 30)
    const { result } = renderHook(() => useFitCount({ current: list }))
    expect(FakeResizeObserver.last?.observe).toHaveBeenCalledWith(list)

    setHeight(list, 'clientHeight', 200)
    act(() => FakeResizeObserver.last?.callback())
    expect(result.current).toBe(6)
  })

  it('stops observing on unmount', () => {
    const { unmount } = renderHook(() =>
      useFitCount({ current: makeList(100, 30) }),
    )
    const observer = FakeResizeObserver.last
    unmount()
    expect(observer?.disconnect).toHaveBeenCalled()
  })
})
