import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../../core/services/auth.service';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-register',
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.scss']
})
export class RegisterComponent {
  registerForm: FormGroup;
  hidePassword = true;
  hideConfirmPassword = true;
  isLoading = false;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private snackBar: MatSnackBar
  ) {
    this.registerForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      confirmPassword: ['', Validators.required],
      firstName: ['', Validators.required],
      lastName: ['', Validators.required]
    }, { validator: this.passwordMatchValidator });
  }

  passwordMatchValidator(g: FormGroup) {
    const pass = g.get('password')?.value;
    const confirmPass = g.get('confirmPassword')?.value;
    return pass === confirmPass ? null : { mismatch: true };
  }

  onSubmit() {
    if (this.registerForm.valid) {
      this.isLoading = true;
      const { confirmPassword, ...userData } = this.registerForm.value;
      
      this.authService.register(userData).subscribe({
        next: (response) => {
          this.isLoading = false;
          this.snackBar.open('Registration successful! Please login.', 'Close', { duration: 5000 });
          this.router.navigate(['/auth/login']);
        },
        error: (error) => {
          this.isLoading = false;
          console.error('Registration failed:', error);
          this.snackBar.open(
            error.error?.message || 'Registration failed. Please try again.',
            'Close',
            { duration: 5000 }
          );
        }
      });
    }
  }
}