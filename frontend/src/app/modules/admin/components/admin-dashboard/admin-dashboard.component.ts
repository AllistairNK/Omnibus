import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-admin-dashboard',
  templateUrl: './admin-dashboard.component.html',
  styleUrls: ['./admin-dashboard.component.scss']
})
export class AdminDashboardComponent implements OnInit {
  navLinks = [
    { path: 'stats', label: 'Statistics', icon: 'assessment' },
    { path: 'users', label: 'User Management', icon: 'people' },
    { path: 'documents', label: 'Document Audit', icon: 'description' },
    { path: 'health', label: 'System Health', icon: 'monitor_heart' },
  ];

  currentTime = new Date();

  constructor(private router: Router) {}

  ngOnInit(): void {
    // Check if we're at the root admin path, redirect to stats
    if (this.router.url === '/admin' || this.router.url === '/admin/') {
      this.router.navigate(['/admin/stats']);
    }
    
    // Update time every minute
    setInterval(() => {
      this.currentTime = new Date();
    }, 60000);
  }
}