import { Component } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.scss']
})
export class SettingsComponent {
  settingsForm: FormGroup;
  selectedTab = 0;

  constructor(private fb: FormBuilder) {
    this.settingsForm = this.fb.group({
      theme: ['terminal'],
      fontSize: [14],
      enableNotifications: [true],
      defaultModel: ['gpt-5-nano'],
      apiEndpoint: ['http://localhost:8000'],
      maxTokens: [2048]
    });
  }

  saveSettings() {
    console.log('Settings saved', this.settingsForm.value);
    // TODO: Implement settings save
  }
}