import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { retry, delay, catchError, throwError, timer } from 'rxjs';

/**
 * Retry interceptor that automatically retries failed HTTP requests
 * with exponential backoff strategy.
 * 
 * Configuration:
 * - Retries up to 3 times for transient errors (5xx, network errors)
 * - Exponential backoff: 1s, 2s, 4s delays
 * - Does not retry 4xx errors (client errors)
 * - Does not retry POST/PUT/DELETE by default (configurable)
 */
export const retryInterceptor: HttpInterceptorFn = (req, next) => {
  // Determine if request should be retried
  const shouldRetry = shouldRetryRequest(req);
  
  if (!shouldRetry) {
    return next(req);
  }

  const maxRetries = 3;
  let retryCount = 0;

  return next(req).pipe(
    retry({
      count: maxRetries,
      delay: (error: HttpErrorResponse, retryCount: number) => {
        // Only retry on specific error types
        if (!isRetryableError(error)) {
          return throwError(() => error);
        }
        
        // Exponential backoff: 1s, 2s, 4s
        const delayMs = Math.pow(2, retryCount) * 1000;
        console.log(`Retry attempt ${retryCount + 1}/${maxRetries} after ${delayMs}ms for ${req.method} ${req.url}`);
        return timer(delayMs);
      }
    }),
    catchError((error: HttpErrorResponse) => {
      // After all retries failed, propagate the error
      console.error(`Request failed after ${maxRetries} retries: ${req.method} ${req.url}`, error);
      return throwError(() => error);
    })
  );
};

/**
 * Determine if a request should be retried based on method and URL
 */
function shouldRetryRequest(req: any): boolean {
  const method = req.method.toUpperCase();
  const url = req.url;
  
  // Don't retry non-idempotent methods by default (can be overridden)
  const nonIdempotentMethods = ['POST', 'PUT', 'PATCH', 'DELETE'];
  if (nonIdempotentMethods.includes(method)) {
    // Check if this is a safe-to-retry endpoint
    const safeToRetryEndpoints = [
      '/api/v1/chats', // Chat creation is idempotent with unique IDs
      '/api/v1/chats/messages', // Message creation
    ];
    
    const isSafeEndpoint = safeToRetryEndpoints.some(endpoint => url.includes(endpoint));
    return isSafeEndpoint;
  }
  
  // Retry GET, HEAD, OPTIONS by default
  return true;
}

/**
 * Determine if an error is retryable
 */
function isRetryableError(error: HttpErrorResponse): boolean {
  // Network errors (status 0) - connection issues
  if (error.status === 0) {
    return true;
  }
  
  // Server errors (5xx) - transient server issues
  if (error.status >= 500 && error.status < 600) {
    return true;
  }
  
  // Rate limiting (429) - can retry after backoff
  if (error.status === 429) {
    return true;
  }
  
  // Gateway timeout (504) - transient
  if (error.status === 504) {
    return true;
  }
  
  // Service unavailable (503) - transient
  if (error.status === 503) {
    return true;
  }
  
  return false;
}