import { Routes } from '@angular/router';
import { AuthGuard } from './core/guards/auth.guard';
import { AdminGuard } from './core/guards/admin.guard';

export const routes: Routes = [
  {
    path: 'auth',
    loadChildren: () => import('./modules/auth/auth.module').then(m => m.AuthModule)
  },
  {
    path: 'chat',
    loadChildren: () => import('./modules/chat/chat.module').then(m => m.ChatModule),
    canActivate: [AuthGuard]
  },
  {
    path: 'documents',
    loadChildren: () => import('./modules/documents/documents.module').then(m => m.DocumentsModule),
    canActivate: [AuthGuard]
  },
  {
    path: 'settings',
    loadChildren: () => import('./modules/settings/settings.module').then(m => m.SettingsModule),
    canActivate: [AuthGuard]
  },
  {
    path: 'admin',
    loadChildren: () => import('./modules/admin/admin.module').then(m => m.AdminModule),
    canActivate: [AuthGuard, AdminGuard]
  },
  { path: '', redirectTo: '/chat', pathMatch: 'full' },
  { path: '**', redirectTo: '/chat' }
];
