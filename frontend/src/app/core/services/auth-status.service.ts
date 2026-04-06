import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export type AuthStatus = 'valid' | 'invalid' | 'expired' | 'unknown';

/**
 * Service to track authentication token status (valid, invalid, expired).
 * Listens to HTTP 401 errors and token presence changes.
 */
@Injectable({
  providedIn: 'root'
})
export class AuthStatusService {
  private authStatusSubject = new BehaviorSubject<AuthStatus>(this.getInitialStatus());
  
  /**
   * Observable of current authentication status.
   */
  public authStatus$: Observable<AuthStatus> = this.authStatusSubject.asObservable();
  
  constructor() {
    // Optionally, we could periodically check token validity
    // For now, we rely on external events (e.g., error interceptor) to update status.
  }
  
  /**
   * Get the current auth status synchronously.
   */
  getCurrentStatus(): AuthStatus {
    return this.authStatusSubject.value;
  }
  
  /**
   * Update auth status (e.g., when a 401 error occurs).
   */
  setStatus(status: AuthStatus): void {
    if (this.authStatusSubject.value !== status) {
      console.log(`AuthStatusService: status changed from ${this.authStatusSubject.value} to ${status}`);
      this.authStatusSubject.next(status);
    }
  }
  
  /**
   * Mark token as invalid (e.g., after receiving a 401 response).
   */
  markInvalid(): void {
    this.setStatus('invalid');
  }
  
  /**
   * Mark token as expired (specific case of invalid).
   */
  markExpired(): void {
    this.setStatus('expired');
  }
  
  /**
   * Mark token as valid (e.g., after successful login).
   */
  markValid(): void {
    this.setStatus('valid');
  }
  
  /**
   * Reset to unknown (e.g., after logout).
   */
  reset(): void {
    this.setStatus('unknown');
  }
  
  /**
   * Determine initial status based on token presence.
   * Note: This does NOT validate token expiration; we assume valid if token exists.
   */
  private getInitialStatus(): AuthStatus {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      return 'unknown';
    }
    // TODO: If we have JWT decoding, we could check expiration here.
    // For now, assume token is valid.
    return 'valid';
  }
}