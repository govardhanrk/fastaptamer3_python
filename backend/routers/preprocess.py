"""
Preprocess Router
API endpoints for sequence preprocessing functionality.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict
import io
import uuid
import tempfile
import os
from pathlib import Path
from services.preprocess_service import PreprocessService

router = APIRouter()

# In-memory storage for uploaded files (use Redis/database in production)
uploaded_files: Dict[str, bytes] = {}
file_metadata: Dict[str, dict] = {}


@router.post("/preprocess/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a FASTA/FASTQ file to the server.
    This is step 1 - just upload and validate the file.
    
    Args:
        file: The uploaded FASTA/FASTQ file (can be gzipped)
        
    Returns:
        JSON response with file_id and metadata
    """
    try:
        # Validate file extension
        valid_extensions = ['.fasta', '.fa', '.fastq', '.fq', '.gz']
        file_ext = file.filename.lower() if file.filename else ''
        
        if not any(file_ext.endswith(ext) for ext in valid_extensions):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Please provide FASTA or FASTQ file."
            )
        
        # Read file content
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty"
            )
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Store file in memory (consider using temp files for large files)
        uploaded_files[file_id] = file_content
        
        # Store metadata
        file_metadata[file_id] = {
            'filename': file.filename,
            'size': len(file_content),
            'content_type': file.content_type
        }
        
        return {
            "success": True,
            "file_id": file_id,
            "filename": file.filename,
            "size": len(file_content),
            "message": "File uploaded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}"
        )


@router.post("/preprocess")
async def preprocess_file(
    file: UploadFile = File(None),
    file_id: Optional[str] = Form(None),
    const5p: str = Form(""),
    const3p: str = Form(""),
    min_length: int = Form(10),
    max_length: int = Form(100),
    max_error: float = Form(0.005)
):
    """
    Preprocess FASTA/FASTQ file.
    This is step 2 - process an uploaded file or a new file.
    
    Args:
        file: The uploaded FASTA/FASTQ file (can be gzipped) - optional if file_id provided
        file_id: ID of previously uploaded file - optional if file provided
        const5p: 5' constant region to trim
        const3p: 3' constant region to trim
        min_length: Minimum sequence length after trimming
        max_length: Maximum sequence length after trimming
        max_error: Maximum allowed average error rate
        
    Returns:
        JSON response with preprocessed sequences
    """
    try:
        # Get file content either from upload or stored file
        file_content = None
        filename = None
        
        if file_id:
            # Use previously uploaded file
            if file_id not in uploaded_files:
                raise HTTPException(
                    status_code=404,
                    detail="File not found. Please upload the file again."
                )
            file_content = uploaded_files[file_id]
            filename = file_metadata[file_id]['filename']
        elif file:
            # Use newly uploaded file (backward compatibility)
            file_content = await file.read()
            filename = file.filename
        else:
            raise HTTPException(
                status_code=400,
                detail="Either file or file_id must be provided"
            )
        
        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="File content is empty"
            )
        
        # Validate inputs
        if min_length < 3 or max_length > 500:
            raise HTTPException(
                status_code=400,
                detail="Length range must be between 3 and 500"
            )
        
        if max_error < 0.001 or max_error > 1:
            raise HTTPException(
                status_code=400,
                detail="Max error must be between 0.001 and 1"
            )
        
        if min_length > max_length:
            raise HTTPException(
                status_code=400,
                detail="Minimum length cannot be greater than maximum length"
            )
        
        # Process sequences
        processed_data = PreprocessService.preprocess_sequences(
            file_content=file_content,
            filename=filename,
            const5p=const5p,
            const3p=const3p,
            length_range=(min_length, max_length),
            max_error=max_error
        )
        
        # Clean up stored file after processing (optional - you may want to keep it)
        # if file_id and file_id in uploaded_files:
        #     del uploaded_files[file_id]
        #     del file_metadata[file_id]
        
        return {
            "success": True,
            "total_sequences": len(processed_data),
            "data": processed_data
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.post("/preprocess/download")
async def download_preprocessed(sequences: List[dict]):
    """
    Download preprocessed sequences as FASTA file.
    
    Args:
        sequences: List of processed sequence dictionaries
        
    Returns:
        FASTA file as downloadable content
    """
    try:
        if not sequences:
            raise HTTPException(
                status_code=400,
                detail="No sequences provided"
            )
        
        # Convert to FASTA format
        fasta_content = PreprocessService.export_to_fasta(sequences)
        
        # Create file stream
        file_stream = io.BytesIO(fasta_content.encode('utf-8'))
        
        return StreamingResponse(
            file_stream,
            media_type="text/plain",
            headers={
                "Content-Disposition": "attachment; filename=preprocessed_sequences.fasta"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating download: {str(e)}"
        )
