import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly TOKEN_KEY = 'auth_token';
  private isAuthenticatedSubject = new BehaviorSubject<boolean>(this.hasToken());

  constructor(private http: HttpClient) {}

  login(email: string, password: string): Observable<any> {
    // TODO: Replace with actual backend endpoint
    return this.http.post('/api/v1/auth/login', { email, password }).pipe(
      tap((response: any) => {
        if (response.token) {
          this.setToken(response.token);
          this.isAuthenticatedSubject.next(true);
        }
      })
    );
  }

  bypassLogin(): void {
    // Set a dummy token to bypass authentication
    const dummyToken = 'dummy_token_bypass_' + Date.now();
    this.setToken(dummyToken);
    this.isAuthenticatedSubject.next(true);
  }

  register(userData: any): Observable<any> {
    return this.http.post('/api/v1/auth/register', userData);
  }

  logout(): void {
    this.removeToken();
    this.isAuthenticatedSubject.next(false);
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
}