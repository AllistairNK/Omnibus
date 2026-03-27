import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface SystemStats {
  total_users: number;
  total_documents: number;
  total_chats: number;
  total_messages: number;
  active_users_24h: number;
  new_users_24h: number;
  storage_used_mb: number;
  api_calls_24h: number;
  avg_response_time_ms: number;
}

export interface DocumentAuditEntry {
  id: string;
  document_id: string;
  user_id: string;
  action: string;
  timestamp: string;
  details: any;
  ip_address?: string;
  user_agent?: string;
}

export interface DocumentAuditResponse {
  entries: DocumentAuditEntry[];
  total: number;
  page: number;
  page_size: number;
}

export interface SystemHealth {
  status: string;
  timestamp: string;
  components: { [key: string]: string };
  metrics: any;
  issues: string[];
}

export interface UserListResponse {
  users: any[];
  total: number;
  page: number;
  page_size: number;
}

export interface UserManagementRequest {
  user_id: string;
  action: string;
  role?: string;
  reason?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AdminService {
  private apiUrl = 'http://localhost:8000/api/v1';

  constructor(private http: HttpClient) {}

  getSystemStats(): Observable<SystemStats> {
    return this.http.get<SystemStats>(`${this.apiUrl}/admin/stats`);
  }

  getDocumentAudit(
    page: number = 1,
    pageSize: number = 50,
    documentId?: string,
    userId?: string,
    action?: string
  ): Observable<DocumentAuditResponse> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());

    if (documentId) params = params.set('document_id', documentId);
    if (userId) params = params.set('user_id', userId);
    if (action) params = params.set('action', action);

    return this.http.get<DocumentAuditResponse>(`${this.apiUrl}/admin/document-audit`, { params });
  }

  getSystemHealth(): Observable<SystemHealth> {
    return this.http.get<SystemHealth>(`${this.apiUrl}/admin/health`);
  }

  getUsers(page: number = 1, pageSize: number = 20): Observable<UserListResponse> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());

    return this.http.get<UserListResponse>(`${this.apiUrl}/users`, { params });
  }

  manageUser(request: UserManagementRequest): Observable<any> {
    return this.http.post(`${this.apiUrl}/admin/users/${request.user_id}/manage`, request);
  }

  getUserById(userId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/users/${userId}`);
  }
}