import boto3, os
import tempfile
from botocore.client import Config
from dotenv import load_dotenv
load_dotenv()

session = boto3.session.Session()
r2 = session.client(
    service_name='s3',
    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
    endpoint_url=os.getenv("R2_ENDPOINT_URL"),
    config=Config(
        signature_version="s3v4",  # IMPORTANT: R2 requires SigV4
        region_name="auto",        # R2 uses "auto" region
        s3={"addressing_style": "path"}  # Force path-style URLs
    )
)
BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "yt-xlate")

def upload_audio_to_r2(file_bytes: bytes, filename: str) -> str:
    r2.put_object(Bucket=BUCKET_NAME, Key=filename, Body=file_bytes, ContentType='audio/mpeg')
    return f"{os.getenv('R2_ENDPOINT_URL')}/{BUCKET_NAME}/{filename}"

def upload_file_to_r2(file_path: str, filename: str) -> str:
    """Upload a local file to R2 and return the public URL"""
    with open(file_path, 'rb') as file:
        r2.put_object(Bucket=BUCKET_NAME, Key=filename, Body=file, ContentType='audio/mpeg')
    return f"{os.getenv('R2_ENDPOINT_URL')}/{BUCKET_NAME}/{filename}"

def download_from_r2(key: str) -> str:
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    r2.download_file(BUCKET_NAME, key, tmp_file.name)
    tmp_file.close()
    return tmp_file.name

def generate_presigned_url(key: str, expiration: int = 3600) -> str:
    """
    Generate a presigned URL for temporary access to an R2 object.
    
    Args:
        key: The R2 object key
        expiration: Expiration time in seconds (default: 3600 = 1 hour)
    
    Returns:
        Temporary download URL that expires after the specified time
    """
    try:
        # Generate presigned URL using boto3
        presigned_url = r2.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': key},
            ExpiresIn=expiration
        )
        
        # Verify the URL contains SigV4 signature
        if 'X-Amz-Algorithm=AWS4-HMAC-SHA256' not in presigned_url:
            print(f"Warning: Generated URL does not contain SigV4 signature: {presigned_url}")
        
        return presigned_url
    except Exception as e:
        print(f"Error generating presigned URL for {key}: {str(e)}")
        raise

def test_r2_connection():
    """
    Test R2 connection and configuration.
    
    Returns:
        Dict with connection status and configuration details
    """
    try:
        # Test basic connection
        response = r2.list_objects_v2(Bucket=BUCKET_NAME, MaxKeys=1)
        
        # Get client configuration
        config = r2._client_config
        
        return {
            "status": "connected",
            "bucket": BUCKET_NAME,
            "endpoint": os.getenv("R2_ENDPOINT_URL"),
            "signature_version": config.signature_version,
            "region": config.region_name,
            "addressing_style": config.s3.get("addressing_style", "unknown"),
            "message": "R2 connection successful"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "bucket": BUCKET_NAME,
            "endpoint": os.getenv("R2_ENDPOINT_URL"),
            "message": "R2 connection failed"
        }

def validate_presigned_url(url: str) -> dict:
    """
    Validate that a presigned URL contains the correct SigV4 signature.
    
    Args:
        url: The presigned URL to validate
    
    Returns:
        Dict with validation results
    """
    validation = {
        "is_valid": False,
        "signature_version": "unknown",
        "expires_in": None,
        "warnings": []
    }
    
    try:
        from urllib.parse import urlparse, parse_qs
        
        # Parse URL
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        # Check for SigV4 signature
        if 'X-Amz-Algorithm' in query_params:
            algorithm = query_params['X-Amz-Algorithm'][0]
            if algorithm == 'AWS4-HMAC-SHA256':
                validation["signature_version"] = "SigV4"
                validation["is_valid"] = True
            else:
                validation["warnings"].append(f"Unexpected algorithm: {algorithm}")
        else:
            validation["warnings"].append("Missing X-Amz-Algorithm parameter")
        
        # Check expiration
        if 'X-Amz-Expires' in query_params:
            validation["expires_in"] = int(query_params['X-Amz-Expires'][0])
        
        # Check for other required SigV4 parameters
        required_params = ['X-Amz-Credential', 'X-Amz-Date', 'X-Amz-SignedHeaders']
        for param in required_params:
            if param not in query_params:
                validation["warnings"].append(f"Missing required parameter: {param}")
                validation["is_valid"] = False
        
        return validation
        
    except Exception as e:
        validation["warnings"].append(f"Validation error: {str(e)}")
        return validation

def cleanup_test_files():
    """
    Clean up test files created during warmup.
    This function can be called periodically to remove test files.
    """
    try:
        # List objects in bucket and remove test files
        response = r2.list_objects_v2(Bucket=BUCKET_NAME, Prefix="warmup_test")
        
        if 'Contents' in response:
            for obj in response['Contents']:
                if obj['Key'].startswith('warmup_test'):
                    r2.delete_object(Bucket=BUCKET_NAME, Key=obj['Key'])
                    print(f"Cleaned up test file: {obj['Key']}")
        
        return {"status": "cleanup_completed", "message": "Test files cleaned up"}
        
    except Exception as e:
        return {"status": "cleanup_failed", "error": str(e)}