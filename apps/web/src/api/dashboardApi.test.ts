// pins the authenticated stream subscriptions: the token goes out as a bearer
// header, only the named event reaches the callback, a server-ended stream is
// turned into a retry, errors reach onError, and disconnecting stops it all.
// fetch-event-source is a fake, so no network or DOM is involved.
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { FetchEventSourceInit } from '@microsoft/fetch-event-source'

import { subscribeToDashboard, subscribeToTrains } from './dashboardApi'

const { fetchEventSource, getAccessToken } = vi.hoisted(() => ({
  fetchEventSource: vi.fn(),
  getAccessToken: vi.fn(),
}))

vi.mock('@microsoft/fetch-event-source', () => ({ fetchEventSource }))
vi.mock('@/api/auth', () => ({ getAccessToken }))

beforeEach(() => {
  fetchEventSource.mockReset().mockReturnValue(new Promise(() => {}))
  getAccessToken.mockReset().mockResolvedValue('test-token')
})

/** Wait for the stream to open and return the url and options it was opened with. */
async function opened(): Promise<[string, FetchEventSourceInit]> {
  await vi.waitFor(() => expect(fetchEventSource).toHaveBeenCalledTimes(1))
  return fetchEventSource.mock.calls[0] as [string, FetchEventSourceInit]
}

function message(event: string, data: string) {
  return { id: '', event, data }
}

describe('subscribeToDashboard', () => {
  it('opens the dashboard stream with the bearer token, also while hidden', async () => {
    subscribeToDashboard(vi.fn())

    const [url, init] = await opened()
    expect(url).toBe('http://localhost:8000/api/v2/dashboard/stream')
    expect(init.headers).toEqual({ Authorization: 'Bearer test-token' })
    expect(init.openWhenHidden).toBe(true)
  })

  it('passes parsed dashboard events to the callback and ignores other events', async () => {
    const callback = vi.fn()
    subscribeToDashboard(callback)
    const [, init] = await opened()

    init.onmessage?.(message('dashboard', '{"time":"2026-11-13T10:00:00Z"}'))
    init.onmessage?.(message('trains', '{"time":"ignored"}'))

    expect(callback).toHaveBeenCalledTimes(1)
    expect(callback).toHaveBeenCalledWith({ time: '2026-11-13T10:00:00Z' })
  })

  it('logs and skips a payload that is not JSON', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
    const callback = vi.fn()
    subscribeToDashboard(callback)
    const [, init] = await opened()

    init.onmessage?.(message('dashboard', 'not json'))

    expect(callback).not.toHaveBeenCalled()
    expect(consoleError).toHaveBeenCalledTimes(1)
    consoleError.mockRestore()
  })

  it('throws when the server ends the stream, so fetch-event-source retries', async () => {
    subscribeToDashboard(vi.fn())
    const [, init] = await opened()

    expect(() => init.onclose?.()).toThrow('The server closed the dashboard stream')
  })

  it('reports connection errors to onError and keeps retrying', async () => {
    const onError = vi.fn()
    subscribeToDashboard(vi.fn(), onError)
    const [, init] = await opened()
    const failure = new Error('network down')

    expect(init.onerror?.(failure)).toBeUndefined()
    expect(onError).toHaveBeenCalledWith(failure)
  })

  it('aborts the stream on disconnect', async () => {
    const disconnect = subscribeToDashboard(vi.fn())
    const [, init] = await opened()

    expect(init.signal?.aborted).toBe(false)
    disconnect()
    expect(init.signal?.aborted).toBe(true)
  })

  it('opens no stream when disconnected before the token arrives', async () => {
    let resolveToken: (token: string) => void = () => {}
    getAccessToken.mockReturnValue(
      new Promise<string>((resolve) => {
        resolveToken = resolve
      }),
    )

    const disconnect = subscribeToDashboard(vi.fn())
    disconnect()
    resolveToken('test-token')
    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(fetchEventSource).not.toHaveBeenCalled()
  })

  it('reports a failure to get the token to onError', async () => {
    const failure = new Error('no token')
    getAccessToken.mockRejectedValue(failure)
    const onError = vi.fn()

    subscribeToDashboard(vi.fn(), onError)

    await vi.waitFor(() => expect(onError).toHaveBeenCalledWith(failure))
    expect(fetchEventSource).not.toHaveBeenCalled()
  })
})

describe('subscribeToTrains', () => {
  it('opens the trains stream and passes only trains events on', async () => {
    const callback = vi.fn()
    subscribeToTrains(callback)
    const [url, init] = await opened()

    init.onmessage?.(message('trains', '{"time":"2026-11-13T10:00:00Z"}'))
    init.onmessage?.(message('dashboard', '{"time":"ignored"}'))

    expect(url).toBe('http://localhost:8000/api/v2/trains/stream')
    expect(init.headers).toEqual({ Authorization: 'Bearer test-token' })
    expect(callback).toHaveBeenCalledExactlyOnceWith({ time: '2026-11-13T10:00:00Z' })
  })
})
