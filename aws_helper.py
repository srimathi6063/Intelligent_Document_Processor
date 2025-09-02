import boto3
import time
import asyncio
from typing import Optional

# Initialize AWS clients only once and reuse
s3 = boto3.client('s3')
textract = boto3.client('textract')

BUCKET_NAME = 'us-aws-test-01'  # Update your bucket name here as needed


def upload_to_s3(file_obj, s3_key):
    try:
        s3.upload_fileobj(file_obj, BUCKET_NAME, s3_key)
        return True
    except Exception as e:
        print(f"S3 Upload error: {e}")
        return False


async def extract_text_from_s3(bucket, key, max_wait_time=300):
    """
    Asynchronously extract text from S3 document using AWS Textract.
    
    Args:
        bucket (str): S3 bucket name
        key (str): S3 object key
        max_wait_time (int): Maximum time to wait for completion in seconds (default: 5 minutes)
    
    Returns:
        str: Extracted text from the document
    """
    print(f"🔍 [AWS TEXTRACT] Starting text extraction from S3")
    print(f"📦 [AWS TEXTRACT] Bucket: {bucket}")
    print(f"📄 [AWS TEXTRACT] Key: {key}")
    print(f"⏱️ [AWS TEXTRACT] Max wait time: {max_wait_time} seconds")
    
    try:
        # Start async text detection job
        print(f"🚀 [AWS TEXTRACT] Starting Textract document text detection job...")
        response = textract.start_document_text_detection(
            DocumentLocation={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key,
                }
            }
        )
        
        job_id = response['JobId']
        print(f"✅ [AWS TEXTRACT] Started Textract job: {job_id}")
        
        # Poll for job completion
        print(f"⏳ [AWS TEXTRACT] Waiting for job completion...")
        extracted_text = await _wait_for_textract_completion(job_id, max_wait_time)
        print(f"✅ [AWS TEXTRACT] Text extraction completed successfully")
        print(f"📏 [AWS TEXTRACT] Extracted text length: {len(extracted_text)} characters")
        print(f"📝 [AWS TEXTRACT] Text preview (first 300 chars): {extracted_text[:300]}...")
        return extracted_text
        
    except Exception as e:
        print(f"❌ [AWS TEXTRACT] Textract async extraction error: {e}")
        raise e


async def _wait_for_textract_completion(job_id: str, max_wait_time: int = 300) -> str:
    """
    Wait for Textract job completion and return extracted text.
    
    Args:
        job_id (str): Textract job ID
        max_wait_time (int): Maximum time to wait in seconds
    
    Returns:
        str: Extracted text from the document
    """
    start_time = time.time()
    wait_time = 5  # Initial wait time in seconds
    
    while True:
        # Check if we've exceeded max wait time
        if time.time() - start_time > max_wait_time:
            raise TimeoutError(f"Textract job {job_id} did not complete within {max_wait_time} seconds")
        
        try:
            # Get job status
            response = textract.get_document_text_detection(JobId=job_id)
            job_status = response['JobStatus']
            
            if job_status == 'SUCCEEDED':
                # Job completed successfully, extract text
                return _extract_text_from_blocks(response.get('Blocks', []))
                
            elif job_status == 'FAILED':
                # Job failed
                error_message = response.get('StatusMessage', 'Unknown error')
                raise Exception(f"Textract job {job_id} failed: {error_message}")
                
            elif job_status == 'IN_PROGRESS':
                # Job still running, wait and check again
                print(f"⏳ [AWS TEXTRACT] Job {job_id} still in progress... (waiting {wait_time}s)")
                await asyncio.sleep(wait_time)
                # Increase wait time for next check (exponential backoff, max 30 seconds)
                wait_time = min(wait_time * 1.5, 30)
                continue
                
            else:
                # Unknown status
                raise Exception(f"Unknown Textract job status: {job_status}")
                
        except Exception as e:
            if "ThrottlingException" in str(e):
                # Handle throttling by waiting longer
                print(f"Textract throttled, waiting {wait_time * 2} seconds...")
                await asyncio.sleep(wait_time * 2)
                wait_time = min(wait_time * 2, 30)
                continue
            else:
                raise e


def _extract_text_from_blocks(blocks):
    """
    Extract text from Textract blocks.
    
    Args:
        blocks (list): List of Textract blocks
    
    Returns:
        str: Extracted text
    """
    extracted_text = ''
    for block in blocks:
        if block.get('BlockType') == 'LINE':
            extracted_text += block.get('Text', '') + '\n'
    return extracted_text.strip()


# Keep the old synchronous function for backward compatibility
def extract_text_from_s3_sync(bucket, key):
    """
    Synchronous version of text extraction (kept for backward compatibility).
    """
    response = textract.detect_document_text(
        Document={
            'S3Object': {
                'Bucket': bucket,
                'Name': key,
            }
        }
    )
    extracted_text = ''
    for block in response.get('Blocks', []):
        if block.get('BlockType') == 'LINE':
            extracted_text += block.get('Text', '') + '\n'
    return extracted_text.strip()
