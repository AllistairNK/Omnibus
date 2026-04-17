import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DigitalRainComponent } from './components/digital-rain/digital-rain.component';

@NgModule({
  declarations: [
    DigitalRainComponent
  ],
  imports: [
    CommonModule
  ],
  exports: [
    DigitalRainComponent
  ]
})
export class SharedModule { }
