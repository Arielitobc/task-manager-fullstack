import { describe, expect, it, vi } from 'vitest'
import { mockFetch } from '../test/utils'
import { ApiError, onUnauthorized, request, tokenStorage } from './client'

describe('api client', () => {
  it('sends the bearer token and query params, skipping empty values', async () => {
    tokenStorage.set('abc')
    const spy = mockFetch({ 'GET /tasks': () => ({ body: { items: [] } }) })
    await request('/tasks', { query: { page: 2, status: undefined, search: '' } })
    const [url, init] = spy.mock.calls[0]
    expect(String(url)).toMatch(/\/tasks\?page=2$/)
    expect((init?.headers as Record<string, string>).Authorization).toBe('Bearer abc')
  })

  it('turns FastAPI validation errors into a readable message', async () => {
    mockFetch({
      'POST /tasks': () => ({
        status: 422,
        body: { detail: [{ loc: ['body', 'title'], msg: 'String should have at least 1 character' }] },
      }),
    })
    await expect(request('/tasks', { method: 'POST', json: {} })).rejects.toThrow(
      'title: String should have at least 1 character',
    )
  })

  it('calls the unauthorized handler on 401 when logged in', async () => {
    tokenStorage.set('expired')
    const handler = vi.fn()
    onUnauthorized(handler)
    mockFetch({ 'GET /auth/me': () => ({ status: 401, body: { detail: 'Invalid or expired token' } }) })
    await expect(request('/auth/me')).rejects.toBeInstanceOf(ApiError)
    expect(handler).toHaveBeenCalledOnce()
    onUnauthorized(null)
  })

  it('reports network failures and rate limiting clearly', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new TypeError('Failed to fetch'))
    await expect(request('/tasks')).rejects.toMatchObject({ status: 0 })

    mockFetch({ 'POST /auth/login': () => ({ status: 429, body: { error: 'Rate limit exceeded' } }) })
    await expect(request('/auth/login', { method: 'POST', form: {} })).rejects.toMatchObject({
      status: 429,
    })
  })

  it('returns undefined for 204 responses', async () => {
    mockFetch({ 'DELETE /tasks/1': () => ({ status: 204 }) })
    await expect(request('/tasks/1', { method: 'DELETE' })).resolves.toBeUndefined()
  })
})
