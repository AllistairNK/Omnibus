import { Injectable } from '@angular/core';
import { Router, ActivatedRouteSnapshot, RouterStateSnapshot, UrlTree } from '@angular/router';
import { Observable } from 'rxjs';
import { map, take } from 'rxjs/operators';
import { Store } from '@ngrx/store';
import { selectUser } from '../state/auth/auth.selectors';

@Injectable({
  providedIn: 'root'
})
export class AdminGuard {
  constructor(
    private router: Router,
    private store: Store
  ) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean | UrlTree> | Promise<boolean | UrlTree> | boolean | UrlTree {
    return this.store.select(selectUser).pipe(
      take(1),
      map(user => {
        // Check if user exists and has admin role
        if (user && (user as any).role === 'admin') {
          return true;
        }
        
        // Redirect to home if not admin
        return this.router.createUrlTree(['/']);
      })
    );
  }
}