import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Store } from '@ngrx/store';
import { selectToken } from '../state/auth/auth.selectors';
import { first, mergeMap } from 'rxjs/operators';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const store = inject(Store);
  return store.select(selectToken).pipe(
    first(),
    mergeMap(token => {
      // Check both NgRx store and localStorage as fallback
      const authToken = token || localStorage.getItem('auth_token');
      if (authToken) {
        const cloned = req.clone({
          setHeaders: {
            Authorization: `Bearer ${authToken}`
          }
        });
        return next(cloned);
      }
      return next(req);
    })
  );
};