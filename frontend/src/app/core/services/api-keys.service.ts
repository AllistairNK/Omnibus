import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface APIKey {
  id: string;
  user_id: string;
  provider: string;
  masked_key: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface APIKeyCreate {
  provider: string;
  api_key: string;
  is_active: boolean;
}

export interface APIKeyUpdate {
  api_key?: string;
  is_active?: boolean;
}

export interface APIKeyListResponse {
  api_keys: APIKey[];
  total: number;
}

@Injectable({
  providedIn: 'root'
})
export class ApiKeysService {
  private readonly baseUrl = '/api/v1/api-keys';

  constructor(private http: HttpClient) {}

  /**
   * Get all API keys for the current user
   */
  getApiKeys(): Observable<APIKeyListResponse> {
    return this.http.get<APIKeyListResponse>(this.baseUrl);
  }

  /**
   * Get a specific API key by ID
   */
  getApiKey(id: string): Observable<APIKey> {
    return this.http.get<APIKey>(`${this.baseUrl}/${id}`);
  }

  /**
   * Create a new API key
   */
  createApiKey(apiKeyData: APIKeyCreate): Observable<APIKey> {
    return this.http.post<APIKey>(this.baseUrl, apiKeyData);
  }

  /**
   * Update an existing API key
   */
  updateApiKey(id: string, apiKeyData: APIKeyUpdate): Observable<APIKey> {
    return this.http.put<APIKey>(`${this.baseUrl}/${id}`, apiKeyData);
  }

  /**
   * Delete an API key
   */
  deleteApiKey(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}`);
  }

  /**
   * Validate an API key format (client-side validation)
   */
  validateApiKeyFormat(provider: string, apiKey: string): { valid: boolean; message?: string } {
    if (!apiKey || apiKey.trim().length === 0) {
      return { valid: false, message: 'API key is required' };
    }

    // Basic length validation
    if (apiKey.length < 10) {
      return { valid: false, message: 'API key appears too short' };
    }

    // Provider-specific validation patterns
    const patterns: Record<string, RegExp> = {
      openai: /^sk-[a-zA-Z0-9]{48,}$/,
      anthropic: /^sk-ant-[a-zA-Z0-9]{48,}$/,
      google: /^AIza[0-9A-Za-z-_]{35}$/,
      azure: /^[a-f0-9]{32}$/i,
    };

    if (patterns[provider]) {
      if (!patterns[provider].test(apiKey)) {
        return { 
          valid: false, 
          message: `API key format doesn't match expected pattern for ${provider}` 
        };
      }
    }

    return { valid: true };
  }

  /**
   * Get available provider options
   */
  getProviders(): Array<{ value: string; label: string; description: string }> {
    return [
      { 
        value: 'openai', 
        label: 'OpenAI', 
        description: 'GPT-4, GPT-3.5, and other OpenAI models' 
      },
      { 
        value: 'anthropic', 
        label: 'Anthropic', 
        description: 'Claude 3, Claude 2, and other Anthropic models' 
      },
      { 
        value: 'google', 
        label: 'Google', 
        description: 'Gemini Pro, Gemini Ultra, and other Google AI models' 
      },
      { 
        value: 'azure', 
        label: 'Azure OpenAI', 
        description: 'Azure-hosted OpenAI models' 
      },
      { 
        value: 'other', 
        label: 'Other', 
        description: 'Custom or other LLM providers' 
      },
    ];
  }

  /**
   * Mask an API key for display (client-side masking)
   */
  maskApiKey(apiKey: string): string {
    if (!apiKey || apiKey.length < 8) {
      return '••••••••';
    }
    
    const visibleChars = 4;
    const maskedPart = '•'.repeat(apiKey.length - visibleChars);
    const visiblePart = apiKey.substring(apiKey.length - visibleChars);
    
    return maskedPart + visiblePart;
  }
}