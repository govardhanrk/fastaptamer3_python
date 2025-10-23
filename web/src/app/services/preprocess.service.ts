import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpEvent, HttpEventType } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface UploadResponse {
  success: boolean;
  file_id: string;
  filename: string;
  size: number;
  message: string;
}

export interface PreprocessRequest {
  file?: File;
  fileId?: string;
  const5p: string;
  const3p: string;
  minLength: number;
  maxLength: number;
  maxError: number;
}

export interface PreprocessedSequence {
  id: string;
  sequence: string;
  length: number;
  quality?: string;
  avg_error?: number;
}

export interface PreprocessResponse {
  success: boolean;
  total_sequences: number;
  data: PreprocessedSequence[];
}

export interface UploadProgress {
  progress: number;
  loaded: number;
  total: number;
}

@Injectable({
  providedIn: 'root'
})
export class PreprocessService {
  private apiUrl = `${environment.apiUrl}/api/v1`;

  constructor(private http: HttpClient) {}

  /**
   * Upload file to server (Step 1)
   * Returns Observable with upload progress
   */
  uploadFile(file: File): Observable<UploadResponse | UploadProgress> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post<UploadResponse>(`${this.apiUrl}/preprocess/upload`, formData, {
      reportProgress: true,
      observe: 'events'
    }).pipe(
      map(event => {
        if (event.type === HttpEventType.UploadProgress) {
          const progress = event.total ? Math.round(100 * event.loaded / event.total) : 0;
          return {
            progress,
            loaded: event.loaded,
            total: event.total || 0
          } as UploadProgress;
        } else if (event.type === HttpEventType.Response) {
          return event.body as UploadResponse;
        }
        return { progress: 0, loaded: 0, total: 0 } as UploadProgress;
      })
    );
  }

  /**
   * Preprocess a previously uploaded file using file_id (Step 2)
   */
  preprocessUploadedFile(fileId: string, params: {
    const5p: string;
    const3p: string;
    minLength: number;
    maxLength: number;
    maxError: number;
  }): Observable<PreprocessResponse> {
    const formData = new FormData();
    formData.append('file_id', fileId);
    formData.append('const5p', params.const5p);
    formData.append('const3p', params.const3p);
    formData.append('min_length', params.minLength.toString());
    formData.append('max_length', params.maxLength.toString());
    formData.append('max_error', params.maxError.toString());

    return this.http.post<PreprocessResponse>(`${this.apiUrl}/preprocess`, formData);
  }

  /**
   * Preprocess a FASTA/FASTQ file (legacy - single step)
   */
  preprocessFile(request: PreprocessRequest): Observable<PreprocessResponse> {
    const formData = new FormData();
    
    if (request.file) {
      formData.append('file', request.file);
    } else if (request.fileId) {
      formData.append('file_id', request.fileId);
    }
    
    formData.append('const5p', request.const5p);
    formData.append('const3p', request.const3p);
    formData.append('min_length', request.minLength.toString());
    formData.append('max_length', request.maxLength.toString());
    formData.append('max_error', request.maxError.toString());

    return this.http.post<PreprocessResponse>(`${this.apiUrl}/preprocess`, formData);
  }

  /**
   * Download preprocessed sequences as FASTA file
   */
  downloadFasta(sequences: PreprocessedSequence[]): Observable<Blob> {
    return this.http.post(`${this.apiUrl}/preprocess/download`, sequences, {
      responseType: 'blob'
    });
  }
}
