import { Component } from '@angular/core';
import { MatTabsModule } from '@angular/material/tabs';
import { Preprocess } from '../preprocess/preprocess';

@Component({
  selector: 'app-start',
  imports: [
    MatTabsModule,
    Preprocess
  ],
  templateUrl: './start.html',
  styleUrl: './start.scss'
})
export class Start {
  selectedTabIndex: number = 0;
}
