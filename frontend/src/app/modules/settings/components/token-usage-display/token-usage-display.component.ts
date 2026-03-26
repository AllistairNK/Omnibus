import { Component, OnInit } from '@angular/core';
import { ModelsService, TokenUsage } from '../../../../core/services/models.service';
import { MatTableDataSource } from '@angular/material/table';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-token-usage-display',
  templateUrl: './token-usage-display.component.html',
  styleUrls: ['./token-usage-display.component.scss']
})
export class TokenUsageDisplayComponent implements OnInit {
  displayedColumns: string[] = ['date', 'model', 'inputTokens', 'outputTokens', 'totalTokens', 'estimatedCost'];
  dataSource = new MatTableDataSource<TokenUsage>();
  totalTokens = 0;
  totalCost = 0;
  isLoading = false;

  constructor(
    private modelsService: ModelsService,
    private snackBar: MatSnackBar
  ) { }

  ngOnInit() {
    this.loadTokenUsage();
  }

  loadTokenUsage() {
    this.isLoading = true;
    this.modelsService.getTokenUsage().subscribe({
      next: (usage) => {
        this.dataSource.data = usage;
        this.totalTokens = usage.reduce((sum, item) => sum + item.inputTokens + item.outputTokens, 0);
        this.totalCost = usage.reduce((sum, item) => sum + item.estimatedCost, 0);
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Failed to load token usage:', error);
        this.snackBar.open('Failed to load token usage data', 'Close', { duration: 3000 });
        this.isLoading = false;
      }
    });
  }

  formatCost(cost: number): string {
    if (cost === 0) return '$0.00';
    if (cost < 0.01) return '< $0.01';
    return `$${cost.toFixed(4)}`;
  }

  formatTokens(tokens: number): string {
    if (tokens >= 1000) {
      return `${(tokens / 1000).toFixed(1)}k`;
    }
    return tokens.toString();
  }

  refresh() {
    this.loadTokenUsage();
  }
}