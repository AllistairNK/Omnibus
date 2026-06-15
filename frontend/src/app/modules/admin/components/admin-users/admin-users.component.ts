import { Component, OnInit } from '@angular/core';
import { AdminService, UserListResponse, UserManagementRequest } from '../../../../core/services/admin.service';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';

export interface User {
  id: string;
  email: string;
  role: string;
  created_at: string;
  last_login?: string;
  is_active: boolean;
}

@Component({
  selector: 'app-admin-users',
  templateUrl: './admin-users.component.html',
  styleUrls: ['./admin-users.component.scss']
})
export class AdminUsersComponent implements OnInit {
  users: User[] = [];
  loading = true;
  error: string | null = null;
  displayedColumns: string[] = ['id', 'email', 'role', 'createdAt', 'actions'];
  totalUsers = 0;
  page = 1;
  pageSize = 20;

  constructor(
    private adminService: AdminService,
    private dialog: MatDialog,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadUsers();
  }

  loadUsers(): void {
    this.loading = true;
    this.error = null;
    
    this.adminService.getUsers(this.page, this.pageSize).subscribe({
      next: (response: UserListResponse) => {
        this.users = response.users;
        this.totalUsers = response.total;
        this.loading = false;
      },
      error: (err: any) => {
        this.error = 'Failed to load users';
        this.loading = false;
        console.error('Error loading users:', err);
      }
    });
  }

  updateUserRole(user: User, newRole: string): void {
    const request: UserManagementRequest = {
      user_id: user.id,
      action: 'change_role',
      role: newRole,
      reason: 'Admin panel update'
    };

    this.adminService.manageUser(request).subscribe({
      next: () => {
        this.snackBar.open(`User role updated to ${newRole}`, 'Close', { duration: 3000 });
        this.loadUsers();
      },
      error: (err: any) => {
        this.snackBar.open('Failed to update user role', 'Close', { duration: 3000 });
        console.error('Error updating user role:', err);
      }
    });
  }

  toggleUserStatus(user: User): void {
    const action = user.is_active ? 'deactivate' : 'activate';
    const request: UserManagementRequest = {
      user_id: user.id,
      action: action,
      reason: 'Admin panel update'
    };

    this.adminService.manageUser(request).subscribe({
      next: () => {
        this.snackBar.open(`User ${action}d successfully`, 'Close', { duration: 3000 });
        this.loadUsers();
      },
      error: (err: any) => {
        this.snackBar.open(`Failed to ${action} user`, 'Close', { duration: 3000 });
        console.error(`Error ${action}ing user:`, err);
      }
    });
  }

  refresh(): void {
    this.loadUsers();
  }

  onPageChange(event: any): void {
    this.page = event.pageIndex + 1;
    this.pageSize = event.pageSize;
    this.loadUsers();
  }

  getActionColor(action: string): string {
    switch (action) {
      case 'create': return 'primary';
      case 'update': return 'accent';
      case 'delete': return 'warn';
      default: return '';
    }
  }

  viewDetails(entry: any): void {
    // Implement view details logic
    console.log('View details:', entry);
  }

  get adminCount(): number {
    return this.users.filter(u => u.role === 'admin').length;
  }

  get activeCount(): number {
    return this.users.filter(u => u.is_active).length;
  }
}