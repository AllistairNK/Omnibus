import { Component, OnInit } from '@angular/core';
import { AdminService, SystemHealth } from '../../../../core/services/admin.service';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-admin-health',
  templateUrl: './admin-health.component.html',
  styleUrls: ['./admin-health.component.scss']
})
export class AdminHealthComponent implements OnInit {
  health: SystemHealth | null = null;
  loading = true;
  error: string | null = null;
  lastUpdated: Date | null = null;

  constructor(
    private adminService: AdminService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadHealth();
  }

  loadHealth(): void {
    this.loading = true;
    this.error = null;
    
    this.adminService.getSystemHealth().subscribe({
      next: (health) => {
        this.health = health;
        this.lastUpdated = new Date();
        this.loading = false;
      },
      error: (err: any) => {
        this.error = 'Failed to load system health';
        this.loading = false;
        console.error('Error loading system health:', err);
      }
    });
  }

  refresh(): void {
    this.loadHealth();
  }

  getStatusColor(status: string): string {
    switch (status.toLowerCase()) {
      case 'healthy': return 'primary';
      case 'degraded': return 'accent';
      case 'unhealthy': return 'warn';
      default: return '';
    }
  }

  getComponentStatusColor(status: string): string {
    switch (status.toLowerCase()) {
      case 'healthy': return 'green';
      case 'degraded': return 'orange';
      case 'unhealthy': return 'red';
      default: return 'gray';
    }
  }

  formatTimestamp(timestamp: string): string {
    return new Date(timestamp).toLocaleString();
  }

  getStatusClass(status: string): string {
    switch (status.toLowerCase()) {
      case 'healthy': return 'status-healthy';
      case 'degraded': return 'status-degraded';
      case 'unhealthy': return 'status-unhealthy';
      default: return '';
    }
  }

  getStatusIcon(status: string): string {
    switch (status.toLowerCase()) {
      case 'healthy': return 'check_circle';
      case 'degraded': return 'warning';
      case 'unhealthy': return 'error';
      default: return 'help';
    }
  }

  getComponents(): any[] {
    if (!this.health?.components) return [];
    return Object.entries(this.health.components).map(([name, status]) => ({
      name,
      status,
      details: ''
    }));
  }

  getComponentStatusClass(status: string): string {
    switch (status.toLowerCase()) {
      case 'healthy': return 'component-healthy';
      case 'degraded': return 'component-degraded';
      case 'unhealthy': return 'component-unhealthy';
      default: return '';
    }
  }

  getComponentIcon(status: string): string {
    switch (status.toLowerCase()) {
      case 'healthy': return 'check_circle';
      case 'degraded': return 'warning';
      case 'unhealthy': return 'error';
      default: return 'help';
    }
  }
}