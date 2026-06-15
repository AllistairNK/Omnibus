import { Component, OnInit } from '@angular/core';
import { AbstractControl, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../../core/services/auth.service';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-forgot-password',
  templateUrl: './forgot-password.component.html',
  styleUrls: ['./forgot-password.component.scss']
})
export class ForgotPasswordComponent implements OnInit {
  forgotPasswordForm: FormGroup;
  resetPasswordForm: FormGroup;
  isLoading = false;
  emailSent = false;
  recoveryToken: string | null = null;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private snackBar: MatSnackBar
  ) {
    this.forgotPasswordForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]]
    });

    this.resetPasswordForm = this.fb.group({
      password: ['', [Validators.required, Validators.minLength(8)]],
      confirmPassword: ['', Validators.required]
    });
    this.resetPasswordForm.addValidators(this.passwordsMatch);
  }

  ngOnInit(): void {
    const hash = window.location.hash;
    if (hash.includes('type=recovery')) {
      const params = new URLSearchParams(hash.slice(1));
      this.recoveryToken = params.get('access_token');
      // Clean the token from the URL without triggering navigation
      window.history.replaceState(null, '', window.location.pathname);
    }
  }

  onSubmit() {
    if (this.forgotPasswordForm.valid) {
      this.isLoading = true;
      const { email } = this.forgotPasswordForm.value;

      this.authService.forgotPassword(email).subscribe({
        next: () => {
          this.isLoading = false;
          this.emailSent = true;
          this.snackBar.open('Password reset email sent! Check your inbox.', 'Close', { duration: 5000 });
        },
        error: (err) => {
          this.isLoading = false;
          const msg = err?.error?.detail || 'Something went wrong. Please try again.';
          this.snackBar.open(msg, 'Close', { duration: 6000 });
        }
      });
    }
  }

  onResetPassword() {
    if (this.resetPasswordForm.valid && this.recoveryToken) {
      this.isLoading = true;
      const { password } = this.resetPasswordForm.value;

      this.authService.resetPassword(this.recoveryToken, password).subscribe({
        next: () => {
          this.isLoading = false;
          this.snackBar.open('Password updated successfully! Please log in.', 'Close', { duration: 5000 });
          this.router.navigate(['/auth/login']);
        },
        error: () => {
          this.isLoading = false;
          this.snackBar.open('Failed to update password. The link may have expired.', 'Close', { duration: 5000 });
        }
      });
    }
  }

  goToLogin() {
    this.router.navigate(['/auth/login']);
  }

  private passwordsMatch(control: AbstractControl) {
    const password = control.get('password')?.value;
    const confirm = control.get('confirmPassword')?.value;
    return password === confirm ? null : { mismatch: true };
  }
}
