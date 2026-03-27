import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AdminDashboardComponent } from './components/admin-dashboard/admin-dashboard.component';
import { AdminUsersComponent } from './components/admin-users/admin-users.component';
import { AdminDocumentsComponent } from './components/admin-documents/admin-documents.component';
import { AdminStatsComponent } from './components/admin-stats/admin-stats.component';
import { AdminHealthComponent } from './components/admin-health/admin-health.component';
import { AdminGuard } from '../../core/guards/admin.guard';

const routes: Routes = [
  {
    path: '',
    component: AdminDashboardComponent,
    canActivate: [AdminGuard],
    children: [
      { path: '', redirectTo: 'stats', pathMatch: 'full' },
      { path: 'stats', component: AdminStatsComponent },
      { path: 'users', component: AdminUsersComponent },
      { path: 'documents', component: AdminDocumentsComponent },
      { path: 'health', component: AdminHealthComponent },
    ]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class AdminRoutingModule { }