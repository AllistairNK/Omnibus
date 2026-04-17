import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../../core/services/auth.service';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent {
  loginForm: FormGroup;
  hidePassword = true;
  isLoading = false;
  matrixMode = false;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private snackBar: MatSnackBar
  ) {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', Validators.required]
    });
  }

  onSubmit() {
    if (this.loginForm.valid) {
      this.isLoading = true;
      const { email, password } = this.loginForm.value;
      
      this.authService.login(email, password).subscribe({
        next: (response) => {
          this.isLoading = false;
          this.snackBar.open('Login successful!', 'Close', { duration: 3000 });
          this.router.navigate(['/chat']);
        },
        error: (error) => {
          this.isLoading = false;
          console.error('Login failed:', error);
          this.snackBar.open(
            error.error?.message || 'Login failed. Please check your credentials.',
            'Close',
            { duration: 5000 }
          );
        }
      });
    }
  }

  onBypassLogin() {
    this.isLoading = true;
    // Simulate a short delay for UX
    setTimeout(() => {
      this.authService.bypassLogin();
      this.isLoading = false;
      this.snackBar.open('Bypass login successful! Using demo account.', 'Close', { duration: 3000 });
      this.router.navigate(['/chat']);
    }, 500);
  }

  onMatrixToggle() {
    // Optional: any side effects when toggling
    console.log('Matrix mode:', this.matrixMode);
  }
}