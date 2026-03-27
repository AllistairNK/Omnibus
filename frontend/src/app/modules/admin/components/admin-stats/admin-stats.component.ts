import { Component, OnInit } from '@angular/core';
import { AdminService, SystemStats } from '../../../../core/services/admin.service';

@Component({
  selector: 'app-admin-stats',
  templateUrl: './admin-stats.component.html',
  styleUrls: ['./admin-stats.component.scss']
})
export class AdminStatsComponent implements OnInit {
  stats: SystemStats | null = null;
  loading = true;
  error: string | null = null;

  constructor(private adminService: AdminService) {}

  ngOnInit(): void {
    this.loadStats();
  }

  loadStats(): void {
    this.loading = true;
    this.error = null;
    
    this.adminService.getSystemStats().subscribe({
      next: (stats) => {
        this.stats = stats;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load system statistics';
        this.loading = false;
        console.error('Error loading stats:', err);
      }
    });
  }

  refresh(): void {
    this.loadStats();
  }
}