import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { MatCardModule } from '@angular/material/card';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';

import { LoginComponent } from './login.component';
import { AuthService } from '../../../../core/services/auth.service';

describe('LoginComponent', () => {
  let component: LoginComponent;
  let fixture: ComponentFixture<LoginComponent>;
  let authService: jasmine.SpyObj<AuthService>;
  let router: Router;

  beforeEach(async () => {
    const authServiceSpy = jasmine.createSpyObj('AuthService', ['login']);
    
    await TestBed.configureTestingModule({
      declarations: [LoginComponent],
      imports: [
        ReactiveFormsModule,
        RouterTestingModule,
        BrowserAnimationsModule,
        MatCardModule,
        MatInputModule,
        MatButtonModule,
        MatIconModule,
        MatProgressSpinnerModule,
        MatSnackBarModule
      ],
      providers: [
        { provide: AuthService, useValue: authServiceSpy }
      ]
    }).compileComponents();

    authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    router = TestBed.inject(Router);
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have a login form with email and password fields', () => {
    expect(component.loginForm).toBeDefined();
    expect(component.loginForm.contains('email')).toBeTrue();
    expect(component.loginForm.contains('password')).toBeTrue();
  });

  it('should make email field required', () => {
    const emailControl = component.loginForm.get('email');
    emailControl?.setValue('');
    expect(emailControl?.valid).toBeFalse();
    expect(emailControl?.errors?.['required']).toBeTruthy();
  });

  it('should validate email format', () => {
    const emailControl = component.loginForm.get('email');
    emailControl?.setValue('invalid-email');
    expect(emailControl?.valid).toBeFalse();
    expect(emailControl?.errors?.['email']).toBeTruthy();
    
    emailControl?.setValue('valid@email.com');
    expect(emailControl?.valid).toBeTrue();
  });

  it('should make password field required', () => {
    const passwordControl = component.loginForm.get('password');
    passwordControl?.setValue('');
    expect(passwordControl?.valid).toBeFalse();
    expect(passwordControl?.errors?.['required']).toBeTruthy();
  });

  it('should call authService.login when form is valid', fakeAsync(() => {
    const mockResponse = { token: 'test-token' };
    authService.login.and.returnValue(of(mockResponse));
    spyOn(router, 'navigate');
    
    component.loginForm.setValue({
      email: 'test@example.com',
      password: 'password123'
    });
    
    component.onSubmit();
    expect(component.isLoading).toBeTrue();
    
    tick(1000); // Simulate async operation
    
    expect(authService.login).toHaveBeenCalledWith('test@example.com', 'password123');
    expect(component.isLoading).toBeFalse();
    expect(router.navigate).toHaveBeenCalledWith(['/chat']);
  }));

  it('should handle login error', fakeAsync(() => {
    const error = { error: { message: 'Invalid credentials' } };
    authService.login.and.returnValue(throwError(() => error));
    
    component.loginForm.setValue({
      email: 'test@example.com',
      password: 'wrongpassword'
    });
    
    component.onSubmit();
    expect(component.isLoading).toBeTrue();
    
    tick(1000); // Simulate async operation
    
    expect(authService.login).toHaveBeenCalled();
    expect(component.isLoading).toBeFalse();
  }));

  it('should not call authService.login when form is invalid', () => {
    component.loginForm.setValue({
      email: '',
      password: ''
    });
    
    component.onSubmit();
    
    expect(authService.login).not.toHaveBeenCalled();
    expect(component.isLoading).toBeFalse();
  });

  it('should toggle password visibility', () => {
    expect(component.hidePassword).toBeTrue();
    
    component.hidePassword = false;
    expect(component.hidePassword).toBeFalse();
    
    component.hidePassword = true;
    expect(component.hidePassword).toBeTrue();
  });
});