import { Injectable } from '@angular/core';
import { HttpClient, HttpEvent, HttpEventType } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { map, tap } from 'rxjs/operators';

export interface Document {
  id: string;
  filename: string;   // ✅ match the backend
  file_size: number;
  file_type: string;
  file_path: string;
  uploaded_at: string;
  processed_at: string | null;
  chunk_count: number;
  status: 'uploaded' | 'processing' | 'processed' | 'failed';
  user_id: string;
  metadata: Record<string, any>;
}

export interface UploadProgress {
  progress: number;
  loaded: number;
  total: number;
  fileName: string;
}

@Injectable({
  providedIn: 'root'
})
export class DocumentsService {
  private readonly API_BASE = '/api/v1';
  private uploadProgress = new BehaviorSubject<UploadProgress | null>(null);
  uploadProgress$ = this.uploadProgress.asObservable();

  constructor(private http: HttpClient) {}

  getDocuments(): Observable<Document[]> {
    return this.http.get<{ documents: Document[] }>(`${this.API_BASE}/documents`).pipe(
      map(response => response.documents)
    );
  }

  uploadDocument(file: File): Observable<HttpEvent<any>> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post(`${this.API_BASE}/documents/upload`, formData, {
      reportProgress: true,
      observe: 'events'
    }).pipe(
      tap(event => {
        if (event.type === HttpEventType.UploadProgress && event.total) {
          this.uploadProgress.next({
            progress: Math.round((100 * event.loaded) / event.total),
            loaded: event.loaded,
            total: event.total,
            fileName: file.name
          });
        } else if (event.type === HttpEventType.Response) {
          this.uploadProgress.next(null);
        }
      })
    );
  }

  deleteDocument(documentId: string): Observable<void> {
    return this.http.delete<void>(`${this.API_BASE}/documents/${documentId}`);
  }

  getDocumentPreview(documentId: string): Observable<{ content: string }> {
    return this.http.get<{ content: string }>(`${this.API_BASE}/documents/${documentId}/preview`);
  }

  getDocumentMetadata(documentId: string): Observable<Document> {
    return this.http.get<Document>(`${this.API_BASE}/documents/${documentId}`);
  }

  clearUploadProgress(): void {
    this.uploadProgress.next(null);
  }
}