import { Component, OnInit } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { DeleteConfirmationDialogComponent } from '../../../documents/components/delete-confirmation-dialog/delete-confirmation-dialog.component';
import { ApiKeysService, APIKey } from '../../../../core/services/api-keys.service';
import { ApiKeyFormComponent } from '../api-key-form/api-key-form.component';

@Component({
  selector: 'app-api-key-list',
  templateUrl: './api-key-list.component.html',
  styleUrls: ['./api-key-list.component.scss']
})
export class ApiKeyListComponent implements OnInit {
  apiKeys: APIKey[] = [];
  isLoading = false;
  isAddingNew = false;
  editingKey: APIKey | null = null;
  displayedColumns: string[] = ['provider', 'masked_key', 'status', 'created', 'actions'];

  constructor(
    private apiKeysService: ApiKeysService,
    private dialog: MatDialog,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit() {
    this.loadApiKeys();
  }

  loadApiKeys() {
    this.isLoading = true;
    this.apiKeysService.getApiKeys().subscribe({
      next: (response) => {
        this.apiKeys = response.api_keys;
        this.isLoading = false;
      },
      error: (error) => {
        this.isLoading = false;
        this.snackBar.open(`Error loading API keys: ${error.message}`, 'Close', { duration: 5000 });
      }
    });
  }

  startAddNew() {
    this.isAddingNew = true;
    this.editingKey = null;
  }

  startEdit(apiKey: APIKey) {
    this.editingKey = apiKey;
    this.isAddingNew = false;
  }

  cancelForm() {
    this.isAddingNew = false;
    this.editingKey = null;
  }

  onApiKeySaved(savedKey: APIKey) {
    this.snackBar.open('API key saved successfully!', 'Close', { duration: 3000 });
    
    // Update the list
    const index = this.apiKeys.findIndex(k => k.id === savedKey.id);
    if (index >= 0) {
      this.apiKeys[index] = savedKey;
    } else {
      this.apiKeys.push(savedKey);
    }
    
    // Reset form states
    this.isAddingNew = false;
    this.editingKey = null;
  }

  confirmDelete(apiKey: APIKey) {
    const dialogRef = this.dialog.open(DeleteConfirmationDialogComponent, {
      width: '400px',
      data: {
        title: 'Delete API Key',
        message: `Are you sure you want to delete the ${apiKey.provider} API key? This action cannot be undone.`,
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel'
      }
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.deleteApiKey(apiKey);
      }
    });
  }

  deleteApiKey(apiKey: APIKey) {
    this.isLoading = true;
    this.apiKeysService.deleteApiKey(apiKey.id).subscribe({
      next: () => {
        this.apiKeys = this.apiKeys.filter(k => k.id !== apiKey.id);
        this.isLoading = false;
        this.snackBar.open('API key deleted successfully!', 'Close', { duration: 3000 });
      },
      error: (error) => {
        this.isLoading = false;
        this.snackBar.open(`Error deleting API key: ${error.message}`, 'Close', { duration: 5000 });
      }
    });
  }

  toggleActive(apiKey: APIKey) {
    const updateData = { is_active: !apiKey.is_active };
    
    this.isLoading = true;
    this.apiKeysService.updateApiKey(apiKey.id, updateData).subscribe({
      next: (updatedKey) => {
        const index = this.apiKeys.findIndex(k => k.id === updatedKey.id);
        if (index >= 0) {
          this.apiKeys[index] = updatedKey;
        }
        this.isLoading = false;
        this.snackBar.open(
          `API key ${updatedKey.is_active ? 'activated' : 'deactivated'} successfully!`, 
          'Close', 
          { duration: 3000 }
        );
      },
      error: (error) => {
        this.isLoading = false;
        this.snackBar.open(`Error updating API key: ${error.message}`, 'Close', { duration: 5000 });
      }
    });
  }

  getProviderIcon(provider: string): string {
    const icons: Record<string, string> = {
      openai: 'smart_toy',
      anthropic: 'psychology',
      google: 'language',
      azure: 'cloud',
      other: 'key'
    };
    return icons[provider] || 'key';
  }

  getProviderLabel(provider: string): string {
    const labels: Record<string, string> = {
      openai: 'OpenAI',
      anthropic: 'Anthropic',
      google: 'Google',
      azure: 'Azure OpenAI',
      other: 'Other'
    };
    return labels[provider] || provider;
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  copyToClipboard(text: string) {
    navigator.clipboard.writeText(text).then(() => {
      this.snackBar.open('Copied to clipboard!', 'Close', { duration: 2000 });
    }).catch(err => {
      console.error('Failed to copy: ', err);
      this.snackBar.open('Failed to copy to clipboard', 'Close', { duration: 3000 });
    });
  }

  get activeKeyCount(): number {
  return this.apiKeys.filter(k => k.is_active).length;
}
}