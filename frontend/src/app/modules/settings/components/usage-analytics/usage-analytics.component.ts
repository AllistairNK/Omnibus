import { Component, OnInit } from '@angular/core';
import { ModelsService, UsageAnalytics } from '../../../../core/services/models.service';
import { MatSnackBar } from '@angular/material/snack-bar';

interface ChartData {
  labels: string[];
  values: number[];
  colors: string[];
}

@Component({
  selector: 'app-usage-analytics',
  templateUrl: './usage-analytics.component.html',
  styleUrls: ['./usage-analytics.component.scss']
})
export class UsageAnalyticsComponent implements OnInit {
  analytics?: UsageAnalytics;
  isLoading = false;
  selectedTimeRange: '7d' | '30d' | '90d' = '7d';
  
  costByModelChart: ChartData = { labels: [], values: [], colors: [] };
  tokenDistributionChart: ChartData = { labels: [], values: [], colors: [] };
  dailyUsageChart: { dates: string[], tokens: number[], costs: number[] } = { dates: [], tokens: [], costs: [] };

  // Color palette for charts
  private colorPalette = [
    '#00ff00', '#0096ff', '#ff6400', '#ffc800', '#64c8ff', '#c864ff', '#969696'
  ];

  constructor(
    private modelsService: ModelsService,
    private snackBar: MatSnackBar
  ) { }

  ngOnInit() {
    this.loadAnalytics();
  }

  loadAnalytics() {
    this.isLoading = true;
    this.modelsService.getUsageAnalytics().subscribe({
      next: (analytics) => {
        this.analytics = analytics;
        this.prepareChartData();
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Failed to load analytics:', error);
        this.snackBar.open('Failed to load analytics data', 'Close', { duration: 3000 });
        this.isLoading = false;
      }
    });
  }

  prepareChartData() {
    if (!this.analytics) return;

    // Prepare cost by model chart
    const modelNames = Object.keys(this.analytics.costByModel);
    const modelCosts = modelNames.map(name => this.analytics!.costByModel[name]);
    
    this.costByModelChart = {
      labels: modelNames,
      values: modelCosts,
      colors: this.colorPalette.slice(0, modelNames.length)
    };

    // Prepare token distribution chart
    const tokenData = modelNames.map(name => this.analytics!.tokensByModel[name]);
    
    this.tokenDistributionChart = {
      labels: modelNames,
      values: tokenData,
      colors: this.colorPalette.slice(0, modelNames.length)
    };

    // Prepare daily usage data
    this.dailyUsageChart = {
      dates: this.analytics.dailyUsage.map(d => d.date),
      tokens: this.analytics.dailyUsage.map(d => d.tokens),
      costs: this.analytics.dailyUsage.map(d => d.cost)
    };
  }

  formatCost(cost: number): string {
    if (cost === 0) return '$0.00';
    if (cost < 0.01) return `$${cost.toFixed(4)}`;
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

  getMaxValue(values: number[]): number {
    return Math.max(...values, 1);
  }

  getBarWidth(value: number, maxValue: number): string {
    const percentage = (value / maxValue) * 100;
    return `${percentage}%`;
  }

  getPieSegment(index: number, total: number): string {
    const percentage = (this.tokenDistributionChart.values[index] / total) * 100;
    return `${percentage}%`;
  }

  changeTimeRange(range: '7d' | '30d' | '90d') {
    this.selectedTimeRange = range;
    // In a real app, this would fetch new data for the selected time range
    this.snackBar.open(`Showing data for last ${range === '7d' ? '7 days' : range === '30d' ? '30 days' : '90 days'}`, 'Close', { duration: 2000 });
  }

  refresh() {
    this.loadAnalytics();
  }

  exportData() {
    // In a real app, this would export analytics data
    this.snackBar.open('Export feature coming soon', 'Close', { duration: 3000 });
  }
}