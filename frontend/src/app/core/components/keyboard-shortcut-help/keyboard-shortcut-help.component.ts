import { Component, OnInit, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatDividerModule } from '@angular/material/divider';
import { KeyboardShortcutService, KeyboardShortcut } from '../../services/keyboard-shortcut.service';

@Component({
  selector: 'app-keyboard-shortcut-help',
  standalone: true,
  imports: [CommonModule, MatDialogModule, MatButtonModule, MatIconModule, MatListModule, MatDividerModule],
  template: `
    <div class="keyboard-shortcut-help">
      <div class="header">
        <h2>Keyboard Shortcuts</h2>
        <button mat-icon-button (click)="close()" aria-label="Close">
          <mat-icon>close</mat-icon>
        </button>
      </div>
      
      <div class="shortcut-list">
        <div *ngFor="let category of categories" class="category">
          <h3>{{ category }}</h3>
          <mat-divider></mat-divider>
          <div class="shortcuts">
            <div *ngFor="let shortcut of shortcutsByCategory[category]" class="shortcut-item">
              <div class="shortcut-keys">
                <span *ngIf="shortcut.ctrlKey" class="key">Ctrl</span>
                <span *ngIf="shortcut.shiftKey" class="key">Shift</span>
                <span *ngIf="shortcut.altKey" class="key">Alt</span>
                <span *ngIf="shortcut.metaKey" class="key">⌘</span>
                <span class="key main-key">{{ shortcut.key.toUpperCase() }}</span>
              </div>
              <div class="shortcut-description">{{ shortcut.description }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="footer">
        <p>Press <span class="key">?</span> to show/hide this help</p>
        <button mat-button (click)="close()">Close</button>
      </div>
    </div>
  `,
  styles: [`
    .keyboard-shortcut-help {
      padding: 20px;
      max-width: 600px;
      max-height: 80vh;
      overflow-y: auto;
      background: var(--background-secondary);
      color: var(--text-primary);
      border-radius: 8px;
      border: 1px solid var(--border-primary);
    }
    
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }
    
    .header h2 {
      margin: 0;
      color: var(--text-accent);
      font-family: 'Courier New', monospace;
    }
    
    .category {
      margin-bottom: 24px;
    }
    
    .category h3 {
      margin: 0 0 8px 0;
      color: var(--text-secondary);
      font-family: 'Courier New', monospace;
      font-size: 16px;
    }
    
    .shortcuts {
      margin-top: 12px;
    }
    
    .shortcut-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 0;
      border-bottom: 1px solid var(--border-secondary);
    }
    
    .shortcut-item:last-child {
      border-bottom: none;
    }
    
    .shortcut-keys {
      display: flex;
      gap: 4px;
      align-items: center;
    }
    
    .key {
      display: inline-block;
      padding: 4px 8px;
      background: var(--background-tertiary);
      color: var(--text-primary);
      border: 1px solid var(--border-secondary);
      border-radius: 4px;
      font-family: 'Courier New', monospace;
      font-size: 12px;
      font-weight: bold;
      min-width: 24px;
      text-align: center;
    }
    
    .main-key {
      background: var(--accent-primary);
      color: var(--background-primary);
      border-color: var(--accent-primary);
    }
    
    .shortcut-description {
      color: var(--text-primary);
      font-size: 14px;
    }
    
    .footer {
      margin-top: 24px;
      padding-top: 16px;
      border-top: 1px solid var(--border-secondary);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .footer p {
      margin: 0;
      color: var(--text-secondary);
      font-size: 14px;
    }
    
    @media (max-width: 768px) {
      .keyboard-shortcut-help {
        padding: 16px;
        max-height: 90vh;
      }
      
      .shortcut-item {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
      }
      
      .footer {
        flex-direction: column;
        gap: 12px;
        text-align: center;
      }
    }
  `]
})
export class KeyboardShortcutHelpComponent implements OnInit {
  shortcutsByCategory: { [category: string]: KeyboardShortcut[] } = {};
  categories: string[] = [];

  constructor(
    private keyboardShortcutService: KeyboardShortcutService,
    private dialogRef: MatDialogRef<KeyboardShortcutHelpComponent>
  ) {}

  ngOnInit(): void {
    this.shortcutsByCategory = this.keyboardShortcutService.getShortcutsByCategory();
    this.categories = Object.keys(this.shortcutsByCategory);
  }

  @HostListener('document:keydown', ['$event'])
  handleKeyboardEvent(event: KeyboardEvent): void {
    if (event.key === 'Escape') {
      this.close();
    } else if (event.key === '?') {
      this.close();
    }
  }

  close(): void {
    this.dialogRef.close();
  }
}