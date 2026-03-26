import { ApplicationConfig, provideZoneChangeDetection, isDevMode, ErrorHandler } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideStore } from '@ngrx/store';
import { provideEffects } from '@ngrx/effects';
import { provideStoreDevtools } from '@ngrx/store-devtools';
import { provideAnimations } from '@angular/platform-browser/animations';

import { routes } from './app.routes';
import { authReducer } from './core/state/auth/auth.reducer';
import { AuthEffects } from './core/state/auth/auth.effects';
import { authInterceptor } from './core/interceptors/auth.interceptor';
import { errorInterceptor } from './core/interceptors/error.interceptor';
import { retryInterceptor } from './core/interceptors/retry.interceptor';
import { GlobalErrorHandlerService } from './core/error-handling/global-error-handler.service';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(
      withInterceptors([authInterceptor, retryInterceptor, errorInterceptor])
    ),
    provideStore({
      auth: authReducer
    }),
    provideEffects([AuthEffects]),
    provideStoreDevtools({ maxAge: 25, logOnly: !isDevMode() }),
    provideAnimations(),
    { provide: ErrorHandler, useClass: GlobalErrorHandlerService }
  ]
};
