import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { Store } from '@ngrx/store';
import * as AuthActions from '../state/auth/auth.actions';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly TOKEN_KEY = 'auth_token';
  private readonly USER_KEY = 'auth_user';
  private isAuthenticatedSubject = new BehaviorSubject<boolean>(this.hasToken());

  constructor(
    private http: HttpClient,
    private store: Store
  ) { }

  login(email: string, password: string): Observable<any> {
    return this.http.post('/api/v1/auth/login', { email, password }).pipe(
      tap((response: any) => {
        if (response.access_token) {                    // was response.token
          this.setToken(response.access_token);         // was response.token
          this.setUser(response.user);
          this.isAuthenticatedSubject.next(true);
          this.store.dispatch(AuthActions.loginSuccess({
            token: response.access_token,
            user: response.user
          }));
        }
      })
    );
  }

  bypassLogin(): void {
    // Set a dummy token to bypass authentication
    const dummyToken = 'dummy_token_bypass_' + Date.now();
    const dummyUser = { email: 'demo@example.com', name: 'Demo User' };
    this.setToken(dummyToken);
    this.setUser(dummyUser);
    this.isAuthenticatedSubject.next(true);
    // Update NgRx store state
    this.store.dispatch(AuthActions.loginSuccess({
      token: dummyToken,
      user: dummyUser
    }));
  }

  register(userData: any): Observable<any> {
    return this.http.post('/api/v1/auth/signup', userData).pipe(
      tap((response: any) => {
        if (response.requires_confirmation) {
          // Show "check your email" message — don't set token
        } else if (response.access_token) {
          this.setToken(response.access_token);
          this.setUser(response.user);
          this.isAuthenticatedSubject.next(true);
          this.store.dispatch(AuthActions.loginSuccess({
            token: response.access_token,
            user: response.user
          }));
        }
      })
    );
  }

  logout(): Observable<any> {
    // Call backend logout endpoint
    return this.http.post('/api/v1/auth/logout', {}).pipe(
      tap(() => {
        this.removeToken();
        this.removeUser();
        this.isAuthenticatedSubject.next(false);
        // Update NgRx store state
        this.store.dispatch(AuthActions.logout());
      }),
      catchError((error) => {
        // Even if backend call fails, clear local auth state
        this.removeToken();
        this.removeUser();
        this.isAuthenticatedSubject.next(false);
        this.store.dispatch(AuthActions.logout());
        return of(null);
      })
    );
  }

  isAuthenticated(): boolean {
    return this.hasToken();
  }

  getAuthStatus(): Observable<boolean> {
    return this.isAuthenticatedSubject.asObservable();
  }

  private setToken(token: string): void {
    if (typeof localStorage === 'undefined') return;
    localStorage.setItem(this.TOKEN_KEY, token);
  }

  private getToken(): string | null {
    if (typeof localStorage === 'undefined') return null;
    return localStorage.getItem(this.TOKEN_KEY);
  }

  private removeToken(): void {
    if (typeof localStorage === 'undefined') return;
    localStorage.removeItem(this.TOKEN_KEY);
  }

  private hasToken(): boolean {
    return !!this.getToken();
  }

  private setUser(user: any): void {
    if (typeof localStorage === 'undefined') return;
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }

  private getUser(): any | null {
    if (typeof localStorage === 'undefined') return null;
    const userJson = localStorage.getItem(this.USER_KEY);
    if (!userJson) return null;
    try {
      return JSON.parse(userJson);
    } catch {
      return null;
    }
  }

  private removeUser(): void {
    if (typeof localStorage === 'undefined') return;
    localStorage.removeItem(this.USER_KEY);
  }
}