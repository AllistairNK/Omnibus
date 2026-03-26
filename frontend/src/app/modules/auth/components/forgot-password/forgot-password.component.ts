import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../../core/services/auth.service';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-forgot-password',
  templateUrl: './forgot-password.component.html',
  styleUrls: ['./forgot-password.component.scss']
})
export class ForgotPasswordComponent {
  forgotPasswordForm: FormGroup;
  isLoading = false;
  emailSent = false;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private snackBar: MatSnackBar
  ) {
    this.forgotPasswordForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]]
    });
  }

  onSubmit() {
    if (this.forgotPasswordForm.valid) {
      this.isLoading = true;
      const { email } = this.forgotPasswordForm.value;
      
      // TODO: Implement forgot password API call
      console.log('Forgot password request for:', email);
      
      // Simulate API call
      setTimeout(() => {
        this.isLoading = false;
        this.emailSent = true;
        this.snackBar.open('Password reset email sent! Check your inbox.', 'Close', { duration: 5000 });
      }, 1500);
    }
  }

  goToLogin() {
    this.router.navigate(['/auth/login']);
  }
}