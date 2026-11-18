// pins authFetch: every request carries the bearer token, and the caller's
// own headers and options survive next to it.
import { afterEach, describe, expect, it, vi } from 'vitest'

import { authFetch } from './authFetch'

vi.mock('@/api/auth', () => ({ getAccessToken: vi.fn().mockResolvedValue('test-token') }))

afterEach(() => {
  vi.unstubAllGlobals()
})

function stubFetch() {
  const fetchMock = vi.fn().mockResolvedValue(new Response('{}', { status: 200 }))
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('authFetch', () => {
  it('sends the access token as a bearer Authorization header', async () => {
    const fetchMock = stubFetch()

    await authFetch('/api/v2/x')

    const headers = new Headers(fetchMock.mock.calls[0][1].headers)
    expect(headers.get('Authorization')).toBe('Bearer test-token')
  })

  it("keeps the caller's headers and options next to the Authorization header", async () => {
    const fetchMock = stubFetch()

    await authFetch('/api/v2/x', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{}',
    })

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/v2/x')
    expect(init.method).toBe('POST')
    expect(init.body).toBe('{}')
    const headers = new Headers(init.headers)
    expect(headers.get('Content-Type')).toBe('application/json')
    expect(headers.get('Authorization')).toBe('Bearer test-token')
  })
})
