import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SettingsRoutingModule } from './settings-routing.module';
import { SettingsComponent } from './components/settings/settings.component';
import { ApiKeyFormComponent } from './components/api-key-form/api-key-form.component';
import { ApiKeyListComponent } from './components/api-key-list/api-key-list.component';
import { TokenUsageDisplayComponent } from './components/token-usage-display/token-usage-display.component';
import { CostEstimatorComponent } from './components/cost-estimator/cost-estimator.component';
import { ModelComparisonComponent } from './components/model-comparison/model-comparison.component';
import { UsageAnalyticsComponent } from './components/usage-analytics/usage-analytics.component';
import { MatCardModule } from '@angular/material/card';
import { MatTabsModule } from '@angular/material/tabs';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialogModule } from '@angular/material/dialog';
import { MatSortModule } from '@angular/material/sort';
import { ReactiveFormsModule } from '@angular/forms';

@NgModule({
  declarations: [
    SettingsComponent,
    ApiKeyFormComponent,
    ApiKeyListComponent,
    TokenUsageDisplayComponent,
    CostEstimatorComponent,
    ModelComparisonComponent,
    UsageAnalyticsComponent
  ],
  imports: [
    CommonModule,
    RouterModule,
    SettingsRoutingModule,
    ReactiveFormsModule,
    MatCardModule,
    MatTabsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatSlideToggleModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatTableModule,
    MatChipsModule,
    MatTooltipModule,
    MatDialogModule,
    MatSortModule 
  ]
})
export class SettingsModule { }