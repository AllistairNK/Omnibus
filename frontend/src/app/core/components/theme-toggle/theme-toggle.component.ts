import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ThemeService, Theme } from '../../services/theme.service';

@Component({
  selector: 'app-theme-toggle',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule, MatTooltipModule],
  template: `
    <button
      mat-icon-button
      [matTooltip]="getTooltipText()"
      (click)="toggleTheme()"
      [attr.aria-label]="getAriaLabel()"
      class="theme-toggle-btn"
      [class.light-theme]="currentTheme === 'light'"
      [class.dark-theme]="currentTheme === 'dark'"
    >
      <mat-icon *ngIf="currentTheme === 'dark'">light_mode</mat-icon>
      <mat-icon *ngIf="currentTheme === 'light'">dark_mode</mat-icon>
    </button>
  `,
  styles: [`
    .theme-toggle-btn {
      transition: all 0.3s ease;
      border-radius: 50%;
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .theme-toggle-btn:hover {
      transform: rotate(15deg) scale(1.1);
      box-shadow: 0 4px 8px var(--card-shadow);
    }
    
    .theme-toggle-btn.dark-theme {
      background-color: var(--button-background);
      color: var(--text-primary);
    }
    
    .theme-toggle-btn.light-theme {
      background-color: var(--button-background);
      color: var(--text-primary);
    }
    
    .theme-toggle-btn:active {
      transform: rotate(0) scale(0.95);
    }
  `]
})
export class ThemeToggleComponent implements OnInit {
  currentTheme: Theme = 'dark';

  constructor(private themeService: ThemeService) {}

  ngOnInit(): void {
    this.currentTheme = this.themeService.getTheme();
  }

  toggleTheme(): void {
    this.themeService.toggleTheme();
    this.currentTheme = this.themeService.getTheme();
  }

  getTooltipText(): string {
    return this.currentTheme === 'dark' 
      ? 'Switch to light theme' 
      : 'Switch to dark theme';
  }

  getAriaLabel(): string {
    return this.currentTheme === 'dark'
      ? 'Switch to light theme'
      : 'Switch to dark theme';
  }
}