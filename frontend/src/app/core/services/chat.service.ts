import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject, fromEvent, merge, of } from 'rxjs';
import { map, catchError, switchMap, takeUntil } from 'rxjs/operators';

export interface ChatMessage {
  id?: string;
  chat_id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
  metadata?: any;
  tokens_used?: number;
  model?: string;
  sources?: Array<{
    document_id: string;
    document_title: string;
    chunk_text: string;
    similarity_score: number;
  }>;
  showSources?: boolean; // UI property for toggling source display
}

export interface ChatSession {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  model_used?: string;
  metadata: any;
  message_count?: number;
}

export interface ChatCompletionRequest {
  message: string;
  chat_id?: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
  use_rag?: boolean;
  include_sources?: boolean;
  rag_method?: string;
}

export interface ChatCompletionResponse {
  chat_id: string;
  message_id: string;
  role: string;
  content: string;
  timestamp: string;
  metadata: any;
  tokens_used?: number;
  model?: string;
  sources?: Array<{
    document_id: string;
    document_title: string;
    chunk_text: string;
    similarity_score: number;
  }>;
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private readonly API_BASE = '/api/v1';
  private eventSource: EventSource | null = null;
  private streamSubject = new Subject<string>();
  private streamCompleteSubject = new Subject<ChatCompletionResponse>();

  constructor(private http: HttpClient) {}

  /**
   * Get all chat sessions for the current user
   */
  getChats(page: number = 1, pageSize: number = 20): Observable<{ chats: ChatSession[], total: number }> {
    return this.http.get<{ chats: ChatSession[], total: number, page: number, page_size: number }>(
      `${this.API_BASE}/chats`,
      { params: { page: page.toString(), page_size: pageSize.toString() } }
    ).pipe(
      map(response => ({
        chats: response.chats,
        total: response.total
      }))
    );
  }

  /**
   * Create a new chat session
   */
  createChat(title?: string, modelUsed?: string): Observable<ChatSession> {
    return this.http.post<ChatSession>(`${this.API_BASE}/chats`, {
      title,
      model_used: modelUsed
    });
  }

  /**
   * Get messages for a specific chat
   */
  getChatMessages(chatId: string, page: number = 1, pageSize: number = 50): Observable<{ messages: ChatMessage[], total: number }> {
    return this.http.get<{ messages: ChatMessage[], total: number, page: number, page_size: number }>(
      `${this.API_BASE}/chats/${chatId}/messages`,
      { params: { page: page.toString(), page_size: pageSize.toString() } }
    ).pipe(
      map(response => ({
        messages: response.messages,
        total: response.total
      }))
    );
  }

  /**
   * Send a message and get a non-streaming response
   */
  sendMessage(request: ChatCompletionRequest): Observable<ChatCompletionResponse> {
    return this.http.post<ChatCompletionResponse>(
      `${this.API_BASE}/chats/completions`,
      { ...request, stream: false }
    );
  }

  /**
   * Send a message and get a streaming response via Server-Sent Events (SSE)
   */
  sendMessageStream(request: ChatCompletionRequest): Observable<{ token: string } | ChatCompletionResponse> {
    // Close any existing connection
    this.closeStream();

    const requestWithStream = { ...request, stream: true };
    
    return new Observable(observer => {
      // First, create the chat completion to get the stream endpoint
      this.http.post<{ stream_url: string }>(
        `${this.API_BASE}/chats/completions/stream/init`,
        requestWithStream
      ).pipe(
        switchMap(response => {
          // Connect to the SSE endpoint
          this.eventSource = new EventSource(response.stream_url);
          
          // Handle incoming tokens
          this.eventSource.addEventListener('token', (event: MessageEvent) => {
            try {
              const data = JSON.parse(event.data);
              observer.next({ token: data.token });
            } catch (error) {
              console.error('Error parsing token event:', error);
            }
          });
          
          // Handle completion
          this.eventSource.addEventListener('complete', (event: MessageEvent) => {
            try {
              const data = JSON.parse(event.data);
              observer.next(data);
              observer.complete();
              this.closeStream();
            } catch (error) {
              console.error('Error parsing complete event:', error);
            }
          });
          
          // Handle errors
          this.eventSource.addEventListener('error', (event: MessageEvent) => {
            console.error('SSE error:', event);
            observer.error(new Error('Stream connection error'));
            this.closeStream();
          });
          
          // Return an observable that completes when the stream ends
          return new Observable(sub => {
            this.eventSource?.addEventListener('close', () => {
              sub.complete();
            });
          });
        }),
        catchError(error => {
          observer.error(error);
          return of(null);
        })
      ).subscribe();
      
      // Cleanup function
      return () => {
        this.closeStream();
      };
    });
  }

  /**
   * Alternative SSE implementation using fetch API for more control
   */
  async *streamMessage(request: ChatCompletionRequest): AsyncGenerator<string, void, unknown> {
    const response = await fetch(`${this.API_BASE}/chats/completions/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify({ ...request, stream: true })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Response body is not readable');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              return;
            }
            try {
              const parsed = JSON.parse(data);
              if (parsed.token) {
                yield parsed.token;
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * Close the current SSE connection
   */
  closeStream(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }

  /**
   * Delete a chat session
   */
  deleteChat(chatId: string): Observable<void> {
    return this.http.delete<void>(`${this.API_BASE}/chats/${chatId}`);
  }

  /**
   * Update a chat session (e.g., change title)
   */
  updateChat(chatId: string, updates: { title?: string }): Observable<ChatSession> {
    return this.http.patch<ChatSession>(`${this.API_BASE}/chats/${chatId}`, updates);
  }

  /**
   * Get stream observable for UI components to subscribe to
   */
  getStreamObservable(): Observable<string> {
    return this.streamSubject.asObservable();
  }

  /**
   * Get stream completion observable
   */
  getStreamCompleteObservable(): Observable<ChatCompletionResponse> {
    return this.streamCompleteSubject.asObservable();
  }
}