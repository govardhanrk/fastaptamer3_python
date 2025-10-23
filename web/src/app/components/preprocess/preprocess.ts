import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatSliderModule } from '@angular/material/slider';
import { MatTableModule } from '@angular/material/table';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatCardModule } from '@angular/material/card';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatIconModule } from '@angular/material/icon';
import { PreprocessService, PreprocessedSequence, UploadResponse, UploadProgress } from '../../services/preprocess.service';

@Component({
  selector: 'app-preprocess',
  imports: [
    CommonModule,
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatSliderModule,
    MatTableModule,
    MatProgressSpinnerModule,
    MatProgressBarModule,
    MatSnackBarModule,
    MatCardModule,
    MatTooltipModule,
    MatIconModule
  ],
  templateUrl: './preprocess.html',
  styleUrl: './preprocess.scss'
})
export class Preprocess {
  // Form inputs
  selectedFile: File | null = null;
  fileName: string = '';
  uploadedFileId: string | null = null;
  const5p: string = '';
  const3p: string = '';
  minLength: number = 10;
  maxLength: number = 54;
  maxError: number = 0.005;

  // State
  isUploading: boolean = false;
  uploadProgress: number = 0;
  isProcessing: boolean = false;
  processedData: PreprocessedSequence[] = [];
  displayedColumns: string[] = ['id', 'sequence', 'length'];

  // Slider formatting
  formatLengthLabel(value: number): string {
    return `${value}`;
  }

  formatErrorLabel(value: number): string {
    return `${value.toFixed(3)}`;
  }

  constructor(
    private preprocessService: PreprocessService,
    private snackBar: MatSnackBar
  ) {}

  /**
   * Handle file selection and start upload
   */
  onFileSelected(event: any): void {
    const file = event.target.files[0];
    if (file) {
      // Validate file extension
      const validExtensions = ['.fasta', '.fa', '.fastq', '.fq', '.gz'];
      const fileName = file.name.toLowerCase();
      const isValid = validExtensions.some(ext => fileName.endsWith(ext));

      if (!isValid) {
        this.snackBar.open('Please select a FASTA or FASTQ file', 'Close', {
          duration: 3000,
          panelClass: ['error-snackbar']
        });
        return;
      }

      this.selectedFile = file;
      this.fileName = file.name;
      this.uploadFile();
    }
  }

  /**
   * Upload file to server (Step 1)
   */
  uploadFile(): void {
    if (!this.selectedFile) {
      return;
    }

    this.isUploading = true;
    this.uploadProgress = 0;
    this.uploadedFileId = null;
    this.processedData = []; // Clear previous results

    this.preprocessService.uploadFile(this.selectedFile).subscribe({
      next: (event) => {
        if ('progress' in event) {
          // Upload progress update
          this.uploadProgress = (event as UploadProgress).progress;
        } else {
          // Upload complete
          const response = event as UploadResponse;
          this.uploadedFileId = response.file_id;
          this.isUploading = false;
          this.uploadProgress = 100;
          
          this.snackBar.open(
            `File uploaded successfully (${this.formatBytes(response.size)})`,
            'Close',
            { duration: 3000, panelClass: ['success-snackbar'] }
          );
        }
      },
      error: (error) => {
        this.isUploading = false;
        this.uploadProgress = 0;
        const errorMsg = error.error?.detail || 'Error uploading file';
        this.snackBar.open(errorMsg, 'Close', {
          duration: 5000,
          panelClass: ['error-snackbar']
        });
      }
    });
  }

  /**
   * Start preprocessing uploaded file (Step 2)
   */
  startPreprocessing(): void {
    if (!this.uploadedFileId) {
      this.snackBar.open('Please upload a file first', 'Close', {
        duration: 3000,
        panelClass: ['error-snackbar']
      });
      return;
    }

    // Validate inputs
    if (this.minLength < 3 || this.maxLength > 500) {
      this.snackBar.open('Length range must be between 3 and 500', 'Close', {
        duration: 3000,
        panelClass: ['error-snackbar']
      });
      return;
    }

    if (this.minLength > this.maxLength) {
      this.snackBar.open('Minimum length cannot be greater than maximum length', 'Close', {
        duration: 3000,
        panelClass: ['error-snackbar']
      });
      return;
    }

    this.isProcessing = true;
    this.processedData = [];

    this.preprocessService.preprocessUploadedFile(this.uploadedFileId, {
      const5p: this.const5p,
      const3p: this.const3p,
      minLength: this.minLength,
      maxLength: this.maxLength,
      maxError: this.maxError
    }).subscribe({
      next: (response) => {
        this.isProcessing = false;
        this.processedData = response.data;

        // Update displayed columns based on data
        if (this.processedData.length > 0 && this.processedData[0].avg_error !== undefined) {
          this.displayedColumns = ['id', 'sequence', 'length', 'avg_error'];
        }

        this.snackBar.open(
          `Successfully processed ${response.total_sequences} sequences`,
          'Close',
          { duration: 3000, panelClass: ['success-snackbar'] }
        );
      },
      error: (error) => {
        this.isProcessing = false;
        const errorMsg = error.error?.detail || 'Error processing file';
        this.snackBar.open(errorMsg, 'Close', {
          duration: 5000,
          panelClass: ['error-snackbar']
        });
      }
    });
  }

  /**
   * Download preprocessed data as FASTA
   */
  downloadResults(): void {
    if (this.processedData.length === 0) {
      this.snackBar.open('No data to download', 'Close', {
        duration: 3000,
        panelClass: ['error-snackbar']
      });
      return;
    }

    this.preprocessService.downloadFasta(this.processedData).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = this.fileName.replace(/\.(fasta|fa|fastq|fq|gz)$/i, '') + '-preprocessed.fasta';
        link.click();
        window.URL.revokeObjectURL(url);

        this.snackBar.open('Download started', 'Close', {
          duration: 2000,
          panelClass: ['success-snackbar']
        });
      },
      error: (error) => {
        this.snackBar.open('Error downloading file', 'Close', {
          duration: 3000,
          panelClass: ['error-snackbar']
        });
      }
    });
  }

  /**
   * Format bytes to human-readable format
   */
  formatBytes(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }

  /**
   * Clear uploaded file and reset
   */
  clearFile(): void {
    this.selectedFile = null;
    this.fileName = '';
    this.uploadedFileId = null;
    this.uploadProgress = 0;
    this.processedData = [];
  }
}
