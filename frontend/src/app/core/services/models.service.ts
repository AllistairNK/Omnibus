import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';

export interface ModelInfo {
  id: string;
  name: string;
  provider: 'openai' | 'anthropic' | 'google' | 'local';
  description: string;
  contextWindow: number;
  maxOutputTokens: number;
  inputCostPer1K: number; // USD per 1K tokens
  outputCostPer1K: number; // USD per 1K tokens
  capabilities: string[];
  speed: 'slow' | 'medium' | 'fast';
  intelligence: 'basic' | 'good' | 'excellent' | 'state-of-the-art';
  lastUpdated: string;
}

export interface TokenUsage {
  date: string;
  modelId: string;
  inputTokens: number;
  outputTokens: number;
  estimatedCost: number;
}

export interface UsageAnalytics {
  totalTokens: number;
  totalCost: number;
  tokensByModel: Record<string, number>;
  costByModel: Record<string, number>;
  dailyUsage: Array<{
    date: string;
    tokens: number;
    cost: number;
  }>;
}

@Injectable({
  providedIn: 'root'
})
export class ModelsService {
  private models: ModelInfo[] = [
    {
      id: 'gpt-5-nano',
      name: 'GPT-5 Nano',
      provider: 'openai',
      description: 'Fastest and most cost-effective GPT-5 model for simple tasks',
      contextWindow: 128000,
      maxOutputTokens: 4096,
      inputCostPer1K: 0.0015,
      outputCostPer1K: 0.002,
      capabilities: ['text-generation', 'chat', 'summarization'],
      speed: 'fast',
      intelligence: 'good',
      lastUpdated: '2026-01-15'
    },
    {
      id: 'gpt-5-turbo',
      name: 'GPT-5 Turbo',
      provider: 'openai',
      description: 'Balanced GPT-5 model with excellent performance for most tasks',
      contextWindow: 128000,
      maxOutputTokens: 16384,
      inputCostPer1K: 0.003,
      outputCostPer1K: 0.006,
      capabilities: ['text-generation', 'chat', 'summarization', 'code-generation'],
      speed: 'medium',
      intelligence: 'excellent',
      lastUpdated: '2026-01-15'
    },
    {
      id: 'claude-3-opus',
      name: 'Claude 3 Opus',
      provider: 'anthropic',
      description: 'Most capable Claude model for complex reasoning tasks',
      contextWindow: 200000,
      maxOutputTokens: 4096,
      inputCostPer1K: 0.015,
      outputCostPer1K: 0.075,
      capabilities: ['text-generation', 'reasoning', 'analysis', 'creative-writing'],
      speed: 'slow',
      intelligence: 'state-of-the-art',
      lastUpdated: '2026-01-10'
    },
    {
      id: 'claude-3-sonnet',
      name: 'Claude 3 Sonnet',
      provider: 'anthropic',
      description: 'Balanced Claude model with strong performance at lower cost',
      contextWindow: 200000,
      maxOutputTokens: 4096,
      inputCostPer1K: 0.003,
      outputCostPer1K: 0.015,
      capabilities: ['text-generation', 'reasoning', 'analysis'],
      speed: 'medium',
      intelligence: 'excellent',
      lastUpdated: '2026-01-10'
    },
    {
      id: 'gemini-pro',
      name: 'Gemini Pro',
      provider: 'google',
      description: 'Google\'s advanced multimodal model with strong reasoning',
      contextWindow: 32768,
      maxOutputTokens: 2048,
      inputCostPer1K: 0.0005,
      outputCostPer1K: 0.0015,
      capabilities: ['text-generation', 'multimodal', 'reasoning'],
      speed: 'fast',
      intelligence: 'good',
      lastUpdated: '2026-01-20'
    },
    {
      id: 'gemini-ultra',
      name: 'Gemini Ultra',
      provider: 'google',
      description: 'Google\'s most capable model for complex tasks',
      contextWindow: 32768,
      maxOutputTokens: 4096,
      inputCostPer1K: 0.0075,
      outputCostPer1K: 0.015,
      capabilities: ['text-generation', 'multimodal', 'advanced-reasoning'],
      speed: 'medium',
      intelligence: 'state-of-the-art',
      lastUpdated: '2026-01-20'
    },
    {
      id: 'local-llama',
      name: 'Local Llama 3',
      provider: 'local',
      description: 'Self-hosted Llama 3 model running locally',
      contextWindow: 8192,
      maxOutputTokens: 2048,
      inputCostPer1K: 0,
      outputCostPer1K: 0,
      capabilities: ['text-generation', 'chat'],
      speed: 'slow',
      intelligence: 'good',
      lastUpdated: '2026-01-05'
    }
  ];

  private mockTokenUsage: TokenUsage[] = [
    { date: '2026-03-25', modelId: 'gpt-5-nano', inputTokens: 1250, outputTokens: 450, estimatedCost: 0.002625 },
    { date: '2026-03-25', modelId: 'claude-3-sonnet', inputTokens: 3200, outputTokens: 1200, estimatedCost: 0.0216 },
    { date: '2026-03-24', modelId: 'gemini-pro', inputTokens: 850, outputTokens: 300, estimatedCost: 0.000725 },
    { date: '2026-03-24', modelId: 'gpt-5-turbo', inputTokens: 2100, outputTokens: 800, estimatedCost: 0.0111 },
    { date: '2026-03-23', modelId: 'gpt-5-nano', inputTokens: 950, outputTokens: 350, estimatedCost: 0.001975 },
    { date: '2026-03-23', modelId: 'local-llama', inputTokens: 4200, outputTokens: 1500, estimatedCost: 0 },
    { date: '2026-03-22', modelId: 'claude-3-opus', inputTokens: 1800, outputTokens: 600, estimatedCost: 0.027 },
    { date: '2026-03-22', modelId: 'gemini-ultra', inputTokens: 1200, outputTokens: 400, estimatedCost: 0.009 },
  ];

  constructor() { }

  getModels(): Observable<ModelInfo[]> {
    return of(this.models);
  }

  getModelById(id: string): Observable<ModelInfo | undefined> {
    const model = this.models.find(m => m.id === id);
    return of(model);
  }

  getTokenUsage(limit?: number): Observable<TokenUsage[]> {
    const usage = this.mockTokenUsage.slice(0, limit);
    return of(usage);
  }

  getUsageAnalytics(): Observable<UsageAnalytics> {
    const totalTokens = this.mockTokenUsage.reduce((sum, usage) => sum + usage.inputTokens + usage.outputTokens, 0);
    const totalCost = this.mockTokenUsage.reduce((sum, usage) => sum + usage.estimatedCost, 0);
    
    const tokensByModel: Record<string, number> = {};
    const costByModel: Record<string, number> = {};
    
    this.mockTokenUsage.forEach(usage => {
      tokensByModel[usage.modelId] = (tokensByModel[usage.modelId] || 0) + usage.inputTokens + usage.outputTokens;
      costByModel[usage.modelId] = (costByModel[usage.modelId] || 0) + usage.estimatedCost;
    });

    // Group by date for daily usage
    const dailyUsageMap: Record<string, { tokens: number, cost: number }> = {};
    this.mockTokenUsage.forEach(usage => {
      if (!dailyUsageMap[usage.date]) {
        dailyUsageMap[usage.date] = { tokens: 0, cost: 0 };
      }
      dailyUsageMap[usage.date].tokens += usage.inputTokens + usage.outputTokens;
      dailyUsageMap[usage.date].cost += usage.estimatedCost;
    });

    const dailyUsage = Object.entries(dailyUsageMap).map(([date, data]) => ({
      date,
      tokens: data.tokens,
      cost: data.cost
    })).sort((a, b) => b.date.localeCompare(a.date));

    return of({
      totalTokens,
      totalCost,
      tokensByModel,
      costByModel,
      dailyUsage
    });
  }

  calculateCost(modelId: string, inputTokens: number, outputTokens: number): number {
    const model = this.models.find(m => m.id === modelId);
    if (!model) return 0;
    
    const inputCost = (inputTokens / 1000) * model.inputCostPer1K;
    const outputCost = (outputTokens / 1000) * model.outputCostPer1K;
    return inputCost + outputCost;
  }

  getModelComparison(): Observable<ModelInfo[]> {
    return of(this.models);
  }

  /**
   * Get the current active model ID
   */
  getCurrentModel(): Observable<string> {
    // In a real app, this would come from user preferences or localStorage
    const savedModel = localStorage.getItem('currentModel') || 'gpt-5-nano';
    return of(savedModel);
  }

  /**
   * Set the current active model
   */
  setCurrentModel(modelId: string): Observable<boolean> {
    // Validate model exists
    const model = this.models.find(m => m.id === modelId);
    if (!model) {
      return of(false);
    }
    
    // Save to localStorage (in a real app, this would be saved to backend)
    localStorage.setItem('currentModel', modelId);
    
    // Also update in-memory state
    this.currentModel = modelId;
    
    return of(true);
  }



  /**
   * Get all available model IDs
   */
  getAvailableModelIds(): Observable<string[]> {
    return of(this.models.map(m => m.id));
  }

  private currentModel: string = 'gpt-5-nano';
}