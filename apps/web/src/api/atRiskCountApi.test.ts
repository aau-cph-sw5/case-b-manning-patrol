import { afterEach, describe, expect, it, vi } from 'vitest'

import { getAtRiskCount } from './atRiskCountApi'

afterEach(() => {
  vi.unstubAllGlobals()
})

function stubFetch(response: Response) {
  const fetchMock = vi.fn().mockResolvedValue(response)
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('getAtRiskCount', () => {
  it('returns the count from the backend', async () => {
    const body = { shift_start: '2026-11-05T22:00:00+01:00', episodes: 7 }
    const fetchMock = stubFetch(new Response(JSON.stringify(body), { status: 200 }))

    await expect(getAtRiskCount()).resolves.toEqual(body)
    expect(fetchMock).toHaveBeenCalledWith('/api/v2/coverage/at-risk-count')
  })

  it("throws the backend's error message", async () => {
    stubFetch(
      new Response(JSON.stringify({ code: 'bad', message: 'Bad shift' }), { status: 400 }),
    )

    await expect(getAtRiskCount()).rejects.toThrow('Bad shift')
  })

  it('falls back to the status when the body is not JSON', async () => {
    stubFetch(new Response('oops', { status: 500 }))

    await expect(getAtRiskCount()).rejects.toThrow('Request failed: 500')
  })
})
