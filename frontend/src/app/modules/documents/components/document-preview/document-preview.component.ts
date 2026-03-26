import { Component, Inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTabsModule } from '@angular/material/tabs';
import { DocumentsService, Document } from '../../../../core/services/documents.service';

export interface DocumentPreviewData {
  document: Document;
}

@Component({
  selector: 'app-document-preview',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatTabsModule
  ],
  templateUrl: './document-preview.component.html',
  styleUrls: ['./document-preview.component.scss']
})
export class DocumentPreviewComponent implements OnInit {
  previewContent: string | null = null;
  isLoading = true;
  error: string | null = null;
  activeTab = 0;

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: DocumentPreviewData,
    private dialogRef: MatDialogRef<DocumentPreviewComponent>,
    private documentsService: DocumentsService
  ) {}

  ngOnInit(): void {
    this.loadPreview();
  }

  loadPreview(): void {
    this.isLoading = true;
    this.error = null;

    this.documentsService.getDocumentPreview(this.data.document.id).subscribe({
      next: (response) => {
        this.previewContent = response.content;
        this.isLoading = false;
      },
      error: (error) => {
        this.error = error.message || 'Failed to load document preview';
        this.isLoading = false;
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

  getFileIcon(): string {
    const fileName = this.data.document.name;
    const extension = fileName.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf': return 'picture_as_pdf';
      case 'txt': return 'description';
      case 'docx': return 'description';
      case 'md': return 'code';
      default: return 'insert_drive_file';
    }
  }

  getStatusColor(): string {
    const status = this.data.document.status.toLowerCase();
    switch (status) {
      case 'processed': return 'success';
      case 'processing': return 'primary';
      case 'uploaded': return 'accent';
      case 'failed': return 'warn';
      default: return '';
    }
  }

  close(): void {
    this.dialogRef.close();
  }
}