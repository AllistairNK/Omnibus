import { Component, OnInit, ViewChild } from '@angular/core';
import { ModelsService, ModelInfo } from '../../../../core/services/models.service';
import { MatTableDataSource } from '@angular/material/table';
import { MatSort } from '@angular/material/sort';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-model-comparison',
  templateUrl: './model-comparison.component.html',
  styleUrls: ['./model-comparison.component.scss']
})
export class ModelComparisonComponent implements OnInit {
  @ViewChild(MatSort) sort!: MatSort;
  
  displayedColumns: string[] = ['name', 'provider', 'contextWindow', 'inputCost', 'outputCost', 'speed', 'intelligence', 'capabilities'];
  dataSource = new MatTableDataSource<ModelInfo>();
  isLoading = false;
  selectedModel?: ModelInfo;
  comparisonModels: ModelInfo[] = [];

  constructor(
    private modelsService: ModelsService,
    private snackBar: MatSnackBar
  ) { }

  ngOnInit() {
    this.loadModels();
  }

  loadModels() {
    this.isLoading = true;
    this.modelsService.getModels().subscribe({
      next: (models) => {
        this.dataSource.data = models;
        this.dataSource.sort = this.sort;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Failed to load models:', error);
        this.snackBar.open('Failed to load models', 'Close', { duration: 3000 });
        this.isLoading = false;
      }
    });
  }

  selectModel(model: ModelInfo) {
    this.selectedModel = model;
  }

  addToComparison(model: ModelInfo) {
    if (!this.comparisonModels.find(m => m.id === model.id)) {
      this.comparisonModels.push(model);
      if (this.comparisonModels.length > 3) {
        this.comparisonModels.shift();
      }
    }
  }

  removeFromComparison(modelId: string) {
    this.comparisonModels = this.comparisonModels.filter(m => m.id !== modelId);
  }

  clearComparison() {
    this.comparisonModels = [];
  }

  formatCost(cost: number): string {
    if (cost === 0) return 'Free';
    if (cost < 0.001) return `$${cost.toFixed(6)}`;
    if (cost < 0.01) return `$${cost.toFixed(4)}`;
    return `$${cost.toFixed(4)}`;
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

  getSpeedIcon(speed: string): string {
    switch (speed) {
      case 'fast': return 'bolt';
      case 'medium': return 'speed';
      case 'slow': return 'hourglass_empty';
      default: return 'help';
    }
  }

  getIntelligenceIcon(intelligence: string): string {
    switch (intelligence) {
      case 'state-of-the-art': return 'psychology';
      case 'excellent': return 'star';
      case 'good': return 'check_circle';
      case 'basic': return 'school';
      default: return 'help';
    }
  }

  getProviderColor(provider: string): string {
    switch (provider) {
      case 'openai': return '#00ff00';
      case 'anthropic': return '#ff6400';
      case 'google': return '#4285f4';
      case 'local': return '#969696';
      default: return '#888';
    }
  }

  applyFilter(event: Event) {
    const filterValue = (event.target as HTMLInputElement).value;
    this.dataSource.filter = filterValue.trim().toLowerCase();
  }
}