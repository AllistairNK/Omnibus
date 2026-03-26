import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { DocumentsService, Document } from '../../../../core/services/documents.service';
import { DocumentPreviewComponent } from '../document-preview/document-preview.component';
import { DeleteConfirmationDialogComponent } from '../delete-confirmation-dialog/delete-confirmation-dialog.component';
import { DocumentUploadComponent } from '../document-upload/document-upload.component';
@Component({
  selector: 'app-document-list',
  standalone: true,
  imports: [
    CommonModule,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatProgressSpinnerModule,
    MatDialogModule,
    MatSnackBarModule,
    DocumentUploadComponent
  ],
  templateUrl: './document-list.component.html',
  styleUrls: ['./document-list.component.scss']
})
export class DocumentListComponent implements OnInit {
  documents: Document[] = [];
  displayedColumns: string[] = ['name', 'type', 'size', 'uploaded', 'chunks', 'status', 'actions'];
  isLoading = true;
  error: string | null = null;

  constructor(
    private documentsService: DocumentsService,
    private dialog: MatDialog,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadDocuments();
  }

  loadDocuments(): void {
    this.isLoading = true;
    this.error = null;
    
    this.documentsService.getDocuments().subscribe({
      next: (documents: Document[]) => {
        this.documents = documents;
        this.isLoading = false;
      },
      error: (error: any) => {
        this.error = error.message || 'Failed to load documents';
        this.isLoading = false;
        this.snackBar.open(this.error!, 'Close', { duration: 5000 });
      }
    });
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  getFileIcon(fileName: string): string {
    const extension = fileName.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf': return 'picture_as_pdf';
      case 'txt': return 'description';
      case 'docx': return 'description';
      case 'md': return 'code';
      default: return 'insert_drive_file';
    }
  }

  getStatusColor(status: string): string {
    switch (status.toLowerCase()) {
      case 'processed': return 'success';
      case 'processing': return 'primary';
      case 'uploaded': return 'accent';
      case 'failed': return 'warn';
      default: return '';
    }
  }

  previewDocument(document: Document): void {
    this.dialog.open(DocumentPreviewComponent, {
      width: '800px',
      maxHeight: '90vh',
      data: { document }
    });
  }

  deleteDocument(document: Document): void {
    const dialogRef = this.dialog.open(DeleteConfirmationDialogComponent, {
      width: '400px',
      data: { 
        title: 'Delete Document',
        message: `Are you sure you want to delete "${document.name}"? This action cannot be undone.`
      }
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.documentsService.deleteDocument(document.id).subscribe({
          next: () => {
            this.snackBar.open('Document deleted successfully', 'Close', { duration: 3000 });
            this.loadDocuments(); // Refresh the list
          },
          error: (error: any) => {
            this.snackBar.open(`Failed to delete document: ${error.message}`, 'Close', { duration: 5000 });
          }
        });
      }
    });
  }

  onUploadComplete(): void {
    this.loadDocuments(); // Refresh the list when upload completes
  }
}