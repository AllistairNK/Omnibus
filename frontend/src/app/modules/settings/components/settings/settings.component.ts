import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { AuthService } from '../../../core/services/auth.service';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.scss']
})
export class SettingsComponent implements OnInit {
  settingsForm: FormGroup;
  profileForm: FormGroup;
  selectedTab = 0;
  isLoading = false;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private snackBar: MatSnackBar
  ) {
    this.settingsForm = this.fb.group({
      theme: ['terminal'],
      fontSize: [14],
      enableNotifications: [true],
      defaultModel: ['gpt-5-nano'],
      apiEndpoint: ['http://localhost:8000'],
      maxTokens: [2048]
    });

    this.profileForm = this.fb.group({
      firstName: ['', Validators.required],
      lastName: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      currentPassword: [''],
      newPassword: ['', Validators.minLength(8)],
      confirmPassword: ['']
    }, { validator: this.passwordMatchValidator });
  }

  ngOnInit() {
    // TODO: Load user profile data from API
    this.loadUserProfile();
  }

  loadUserProfile() {
    // Mock user data - replace with actual API call
    const mockUser = {
      firstName: 'John',
      lastName: 'Doe',
      email: 'john.doe@example.com'
    };
    this.profileForm.patchValue(mockUser);
  }

  passwordMatchValidator(g: FormGroup) {
    const newPass = g.get('newPassword')?.value;
    const confirmPass = g.get('confirmPassword')?.value;
    if (newPass && confirmPass && newPass !== confirmPass) {
      return { mismatch: true };
    }
    return null;
  }

  saveSettings() {
    this.isLoading = true;
    console.log('Settings saved', this.settingsForm.value);
    // TODO: Implement settings save API call
    setTimeout(() => {
      this.isLoading = false;
      this.snackBar.open('Settings saved successfully!', 'Close', { duration: 3000 });
    }, 1000);
  }

  saveProfile() {
    if (this.profileForm.valid) {
      this.isLoading = true;
      const profileData = this.profileForm.value;
      console.log('Profile saved', profileData);
      // TODO: Implement profile update API call
      setTimeout(() => {
        this.isLoading = false;
        this.snackBar.open('Profile updated successfully!', 'Close', { duration: 3000 });
      }, 1000);
    }
  }

  changePassword() {
    const { currentPassword, newPassword } = this.profileForm.value;
    if (!currentPassword || !newPassword) {
      this.snackBar.open('Please fill in current and new password', 'Close', { duration: 3000 });
      return;
    }
    
    this.isLoading = true;
    console.log('Changing password...');
    // TODO: Implement password change API call
    setTimeout(() => {
      this.isLoading = false;
      this.snackBar.open('Password changed successfully!', 'Close', { duration: 3000 });
      this.profileForm.patchValue({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      });
    }, 1000);
  }
}