import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ModelsService, ModelInfo } from '../../../../core/services/models.service';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-cost-estimator',
  templateUrl: './cost-estimator.component.html',
  styleUrls: ['./cost-estimator.component.scss']
})
export class CostEstimatorComponent implements OnInit {
  estimatorForm: FormGroup;
  models: ModelInfo[] = [];
  selectedModel?: ModelInfo;
  estimatedCost = 0;
  isLoading = false;

  constructor(
    private fb: FormBuilder,
    private modelsService: ModelsService,
    private snackBar: MatSnackBar
  ) {
    this.estimatorForm = this.fb.group({
      modelId: ['gpt-5-nano', Validators.required],
      inputTokens: [1000, [Validators.required, Validators.min(1), Validators.max(1000000)]],
      outputTokens: [500, [Validators.required, Validators.min(1), Validators.max(100000)]],
      numberOfQueries: [1, [Validators.required, Validators.min(1), Validators.max(10000)]]
    });
  }

  ngOnInit() {
    this.loadModels();
    this.onFormChanges();
  }

  loadModels() {
    this.isLoading = true;
    this.modelsService.getModels().subscribe({
      next: (models) => {
        this.models = models;
        this.updateSelectedModel();
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Failed to load models:', error);
        this.snackBar.open('Failed to load models', 'Close', { duration: 3000 });
        this.isLoading = false;
      }
    });
  }

  onFormChanges() {
    this.estimatorForm.valueChanges.subscribe(() => {
      this.updateSelectedModel();
      this.calculateCost();
    });
  }

  updateSelectedModel() {
    const modelId = this.estimatorForm.get('modelId')?.value;
    this.selectedModel = this.models.find(m => m.id === modelId);
  }

  calculateCost() {
    if (!this.selectedModel) return;

    const inputTokens = this.estimatorForm.get('inputTokens')?.value || 0;
    const outputTokens = this.estimatorForm.get('outputTokens')?.value || 0;
    const numberOfQueries = this.estimatorForm.get('numberOfQueries')?.value || 1;

    const inputCost = (inputTokens / 1000) * this.selectedModel.inputCostPer1K;
    const outputCost = (outputTokens / 1000) * this.selectedModel.outputCostPer1K;
    const costPerQuery = inputCost + outputCost;
    
    this.estimatedCost = costPerQuery * numberOfQueries;
  }

  formatCost(cost: number): string {
    if (cost === 0) return '$0.00';
    if (cost < 0.0001) return '< $0.0001';
    if (cost < 0.01) return `$${cost.toFixed(6)}`;
    if (cost < 1) return `$${cost.toFixed(4)}`;
    return `$${cost.toFixed(2)}`;
  }

  formatTokens(tokens: number): string {
    if (tokens >= 1000000) {
      return `${(tokens / 1000000).toFixed(1)}M`;
    }
    if (tokens >= 1000) {
      return `${(tokens / 1000).toFixed(1)}k`;
    }
    return tokens.toString();
  }

  getCostBreakdown() {
    if (!this.selectedModel) return { inputCost: 0, outputCost: 0, perQuery: 0 };
    
    const inputTokens = this.estimatorForm.get('inputTokens')?.value || 0;
    const outputTokens = this.estimatorForm.get('outputTokens')?.value || 0;
    
    const inputCost = (inputTokens / 1000) * this.selectedModel.inputCostPer1K;
    const outputCost = (outputTokens / 1000) * this.selectedModel.outputCostPer1K;
    const perQuery = inputCost + outputCost;
    
    return { inputCost, outputCost, perQuery };
  }

  resetToDefaults() {
    this.estimatorForm.patchValue({
      inputTokens: 1000,
      outputTokens: 500,
      numberOfQueries: 1
    });
  }

  setExample(example: 'short' | 'medium' | 'long') {
    switch (example) {
      case 'short':
        this.estimatorForm.patchValue({
          inputTokens: 500,
          outputTokens: 200,
          numberOfQueries: 10
        });
        break;
      case 'medium':
        this.estimatorForm.patchValue({
          inputTokens: 2000,
          outputTokens: 800,
          numberOfQueries: 100
        });
        break;
      case 'long':
        this.estimatorForm.patchValue({
          inputTokens: 8000,
          outputTokens: 3000,
          numberOfQueries: 1000
        });
        break;
    }
  }
}