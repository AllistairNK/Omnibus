import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ApiKeysService, APIKey, APIKeyCreate, APIKeyUpdate } from '../../../../core/services/api-keys.service';

@Component({
  selector: 'app-api-key-form',
  templateUrl: './api-key-form.component.html',
  styleUrls: ['./api-key-form.component.scss'],
})
export class ApiKeyFormComponent implements OnInit {
  @Input() apiKey?: APIKey;
  @Input() isEditing = false;
  @Output() saved = new EventEmitter<APIKey>();
  @Output() cancelled = new EventEmitter<void>();

  apiKeyForm: FormGroup;
  providers: Array<{ value: string; label: string; description: string }> = [];
  isLoading = false;
  showApiKey = false;
  validationError = '';

  constructor(
    private fb: FormBuilder,
    private apiKeysService: ApiKeysService,
    private snackBar: MatSnackBar
  ) {
    this.apiKeyForm = this.fb.group({
      provider: ['', Validators.required],
      api_key: ['', Validators.required],
      is_active: [true]
    });
  }

  ngOnInit() {
    this.providers = this.apiKeysService.getProviders();
    
    if (this.apiKey && this.isEditing) {
      this.populateForm();
    }
    
    // Watch for provider changes to update validation
    this.apiKeyForm.get('provider')?.valueChanges.subscribe(() => {
      this.validateApiKey();
    });
    
    this.apiKeyForm.get('api_key')?.valueChanges.subscribe(() => {
      this.validateApiKey();
    });
  }

  private populateForm() {
    if (!this.apiKey) return;
    
    // For editing, we don't show the actual API key (it's masked from backend)
    // User needs to enter a new key if they want to update it
    this.apiKeyForm.patchValue({
      provider: this.apiKey.provider,
      api_key: '', // Empty for editing - user must enter new key if they want to change it
      is_active: this.apiKey.is_active
    });
  }

  validateApiKey() {
    const provider = this.apiKeyForm.get('provider')?.value;
    const apiKey = this.apiKeyForm.get('api_key')?.value;
    
    if (!provider || !apiKey) {
      this.validationError = '';
      return;
    }
    
    const validation = this.apiKeysService.validateApiKeyFormat(provider, apiKey);
    if (!validation.valid) {
      this.validationError = validation.message || 'Invalid API key format';
    } else {
      this.validationError = '';
    }
  }

  toggleShowApiKey() {
    this.showApiKey = !this.showApiKey;
  }

  onSubmit() {
    if (this.apiKeyForm.invalid) {
      this.markFormGroupTouched(this.apiKeyForm);
      return;
    }

    if (this.validationError) {
      this.snackBar.open(this.validationError, 'Close', { duration: 3000 });
      return;
    }

    this.isLoading = true;
    const formData = this.apiKeyForm.value;

    if (this.isEditing && this.apiKey) {
      const updateData: APIKeyUpdate = {
        is_active: formData.is_active
      };
      
      // Only include api_key if it was provided (not empty)
      if (formData.api_key && formData.api_key.trim().length > 0) {
        updateData.api_key = formData.api_key;
      }
      
      this.apiKeysService.updateApiKey(this.apiKey.id, updateData).subscribe({
        next: (updatedKey) => {
          this.isLoading = false;
          this.snackBar.open('API key updated successfully!', 'Close', { duration: 3000 });
          this.saved.emit(updatedKey);
        },
        error: (error) => {
          this.isLoading = false;
          this.snackBar.open(`Error updating API key: ${error.message}`, 'Close', { duration: 5000 });
        }
      });
    } else {
      const createData: APIKeyCreate = {
        provider: formData.provider,
        api_key: formData.api_key,
        is_active: formData.is_active
      };
      
      this.apiKeysService.createApiKey(createData).subscribe({
        next: (newKey) => {
          this.isLoading = false;
          this.snackBar.open('API key created successfully!', 'Close', { duration: 3000 });
          this.saved.emit(newKey);
          this.apiKeyForm.reset({ provider: '', api_key: '', is_active: true });
        },
        error: (error) => {
          this.isLoading = false;
          this.snackBar.open(`Error creating API key: ${error.message}`, 'Close', { duration: 5000 });
        }
      });
    }
  }

  onCancel() {
    this.cancelled.emit();
  }

  private markFormGroupTouched(formGroup: FormGroup) {
    Object.values(formGroup.controls).forEach(control => {
      control.markAsTouched();
      
      if (control instanceof FormGroup) {
        this.markFormGroupTouched(control);
      }
    });
  }

  get providerControl() {
    return this.apiKeyForm.get('provider');
  }

  get apiKeyControl() {
    return this.apiKeyForm.get('api_key');
  }

  get isActiveControl() {
    return this.apiKeyForm.get('is_active');
  }
}