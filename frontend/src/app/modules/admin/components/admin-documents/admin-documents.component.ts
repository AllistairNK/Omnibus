import { Component, OnInit } from '@angular/core';
import { AdminService, DocumentAuditResponse, DocumentAuditEntry } from '../../../../core/services/admin.service';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-admin-documents',
  templateUrl: './admin-documents.component.html',
  styleUrls: ['./admin-documents.component.scss']
})
export class AdminDocumentsComponent implements OnInit {
  auditEntries: DocumentAuditEntry[] = [];
  loading = true;
  error: string | null = null;
  displayedColumns: string[] = ['id', 'document_id', 'user_id', 'action', 'timestamp', 'details'];
  totalEntries = 0;
  page = 1;
  pageSize = 20;
  
  // Filters
  documentIdFilter = '';
  userIdFilter = '';
  actionFilter = '';

  constructor(
    private adminService: AdminService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadAuditEntries();
  }

  loadAuditEntries(): void {
    this.loading = true;
    this.error = null;
    
    this.adminService.getDocumentAudit(
      this.page,
      this.pageSize,
      this.documentIdFilter || undefined,
      this.userIdFilter || undefined,
      this.actionFilter || undefined
    ).subscribe({
      next: (response: DocumentAuditResponse) => {
        this.auditEntries = response.entries;
        this.totalEntries = response.total;
        this.loading = false;
      },
      error: (err: any) => {
        this.error = 'Failed to load document audit entries';
        this.loading = false;
        console.error('Error loading audit entries:', err);
      }
    });
  }

  applyFilters(): void {
    this.page = 1;
    this.loadAuditEntries();
  }

  clearFilters(): void {
    this.documentIdFilter = '';
    this.userIdFilter = '';
    this.actionFilter = '';
    this.page = 1;
    this.loadAuditEntries();
  }

  refresh(): void {
    this.loadAuditEntries();
  }

  onPageChange(event: any): void {
    this.page = event.pageIndex + 1;
    this.pageSize = event.pageSize;
    this.loadAuditEntries();
  }

  getActionIcon(action: string): string {
    switch (action.toLowerCase()) {
      case 'upload': return 'cloud_upload';
      case 'delete': return 'delete';
      case 'view': return 'visibility';
      case 'download': return 'file_download';
      case 'update': return 'edit';
      default: return 'description';
    }
  }

  getActionColor(action: string): string {
    switch (action.toLowerCase()) {
      case 'upload': return 'primary';
      case 'delete': return 'warn';
      case 'view': return 'accent';
      case 'download': return 'primary';
      case 'update': return 'accent';
      default: return '';
    }
  }

  viewDetails(entry: any): void {
    console.log('View details:', entry);
    // Implement dialog or side panel for details
  }
}