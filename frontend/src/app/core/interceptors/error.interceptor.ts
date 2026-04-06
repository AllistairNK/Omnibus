import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthStatusService } from '../services/auth-status.service';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const authStatusService = inject(AuthStatusService);
  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401) {
        // Unauthorized - token invalid or expired
        const detail = error.error?.detail || '';
        if (detail.includes('expired')) {
          authStatusService.markExpired();
        } else {
          authStatusService.markInvalid();
        }
        // Redirect to login
        router.navigate(['/auth/login']);
      } else if (error.status === 403) {
        // Forbidden
        console.error('Access forbidden:', error.message);
      } else if (error.status >= 500) {
        // Server error
        console.error('Server error:', error.message);
      }
      // Propagate the error
      return throwError(() => error);
    })
  );
};