import { Component, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { AdminService, UserManagementRequest } from '../../../../core/services/admin.service';

export interface UserManagementDialogData {
  user: {
    id: string;
    email: string;
    role: string;
    is_active: boolean;
  };
}

@Component({
  selector: 'app-user-management-dialog',
  templateUrl: './user-management-dialog.component.html',
  styleUrls: ['./user-management-dialog.component.scss']
})
export class UserManagementDialogComponent {
  loading = false;
  roles = ['admin', 'user'];
  selectedRole: string;
  isActive: boolean;

  constructor(
    public dialogRef: MatDialogRef<UserManagementDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: UserManagementDialogData,
    private adminService: AdminService,
    private snackBar: MatSnackBar
  ) {
    this.selectedRole = data.user.role;
    this.isActive = data.user.is_active;
  }

  onCancel(): void {
    this.dialogRef.close();
  }

  onSave(): void {
    this.loading = true;
    const request: UserManagementRequest = {
      user_id: this.data.user.id,
      action: 'update',
      role: this.selectedRole
    };

    this.adminService.manageUser(request).subscribe({
      next: () => {
        this.snackBar.open('User updated successfully', 'Close', { duration: 3000 });
        this.dialogRef.close(true);
      },
      error: (error: any) => {
        console.error('Failed to update user:', error);
        this.snackBar.open('Failed to update user', 'Close', { duration: 3000 });
        this.loading = false;
      }
    });
  }
}