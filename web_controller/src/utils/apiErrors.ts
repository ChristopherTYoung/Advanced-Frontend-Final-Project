import { z } from 'zod'

export class ValidationError extends Error {
  zodError?: z.ZodError

  constructor(
    message: string,
    zodError?: z.ZodError
  ) {
    super(message)
    this.name = 'ValidationError'
    this.zodError = zodError
  }

  getErrors(): Record<string, string[]> {
    if (!this.zodError) return {}

    const errors: Record<string, string[]> = {}
    
    for (const issue of this.zodError.issues) {
      const path = issue.path.join('.')
      if (!errors[path]) {
        errors[path] = []
      }
      errors[path].push(issue.message)
    }

    return errors
  }

  getUserMessage(): string {
    if (!this.zodError) return this.message

    const firstIssue = this.zodError.issues[0]
    const field = firstIssue.path.join('.')
    return `${field}: ${firstIssue.message}`
  }
}

export class ApiError extends Error {
  statusCode?: number
  details?: string

  constructor(
    message: string,
    statusCode?: number,
    details?: string
  ) {
    super(message)
    this.name = 'ApiError'
    this.statusCode = statusCode
    this.details = details
  }
}

export async function handleApiError(response: Response): Promise<never> {
  let errorMessage = 'An error occurred'
  let details: string | undefined

  try {
    const data = await response.json()
    errorMessage = data.error || data.message || errorMessage
    details = data.detail
  } catch {
    // If response is not JSON, use status text
    errorMessage = response.statusText || errorMessage
  }

  throw new ApiError(errorMessage, response.status, details)
}
