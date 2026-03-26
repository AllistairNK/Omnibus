import { Component, Output, EventEmitter, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatCardModule } from '@angular/material/card';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { DocumentsService, UploadProgress } from '../../../../core/services/documents.service';

@Component({
  selector: 'app-document-upload',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatCardModule,
    MatSnackBarModule
  ],
  templateUrl: './document-upload.component.html',
  styleUrls: ['./document-upload.component.scss']
})
export class DocumentUploadComponent {
  @Output() uploadComplete = new EventEmitter<void>();
  
  isDragging = false;
  selectedFile: File | null = null;
  uploadProgress: UploadProgress | null = null;
  isUploading = false;
  acceptedFileTypes = '.pdf,.txt,.docx,.md';
  maxFileSize = 10 * 1024 * 1024; // 10MB

  constructor(
    private documentsService: DocumentsService,
    private snackBar: MatSnackBar
  ) {}

  @HostListener('dragover', ['$event'])
  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = true;
  }

  @HostListener('dragleave', ['$event'])
  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
  }

  @HostListener('drop', ['$event'])
  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;

    if (event.dataTransfer?.files.length) {
      this.handleFileSelection(event.dataTransfer.files[0]);
    }
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files?.length) {
      this.handleFileSelection(input.files[0]);
    }
  }

  handleFileSelection(file: File): void {
    // Validate file type
    const fileExtension = file.name.split('.').pop()?.toLowerCase();
    const allowedExtensions = ['pdf', 'txt', 'docx', 'md'];
    
    if (!fileExtension || !allowedExtensions.includes(fileExtension)) {
      this.snackBar.open(
        `Invalid file type. Allowed types: ${allowedExtensions.join(', ')}`,
        'Close',
        { duration: 5000 }
      );
      return;
    }

    // Validate file size
    if (file.size > this.maxFileSize) {
      this.snackBar.open(
        `File too large. Maximum size: ${this.maxFileSize / (1024 * 1024)}MB`,
        'Close',
        { duration: 5000 }
      );
      return;
    }

    this.selectedFile = file;
  }

  uploadFile(): void {
    if (!this.selectedFile) return;

    this.isUploading = true;
    this.documentsService.uploadDocument(this.selectedFile).subscribe({
      next: (event) => {
        // Progress updates are handled by the service observable
        if (event.type === 4) { // HttpEventType.Response
          this.isUploading = false;
          this.selectedFile = null;
          this.uploadComplete.emit();
          this.snackBar.open('Document uploaded successfully!', 'Close', { duration: 3000 });
        }
      },
      error: (error) => {
        this.isUploading = false;
        this.snackBar.open(
          `Upload failed: ${error.error?.message || error.message}`,
          'Close',
          { duration: 5000 }
        );
      }
    });

    // Subscribe to progress updates
    this.documentsService.uploadProgress$.subscribe(progress => {
      this.uploadProgress = progress;
    });
  }

  removeFile(): void {
    this.selectedFile = null;
    this.uploadProgress = null;
    this.documentsService.clearUploadProgress();
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
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
}