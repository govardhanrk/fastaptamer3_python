import { TestBed } from '@angular/core/testing';
import { Preprocess } from './preprocess';

describe('Preprocess', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Preprocess]
    }).compileComponents();
  });

  it('should create the component', () => {
    const fixture = TestBed.createComponent(Preprocess);
    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
  });
});
