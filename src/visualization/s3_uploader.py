"""S3 upload utilities for storing visualization outputs."""

from typing import Optional
import boto3
from botocore.exceptions import ClientError
import os
from datetime import datetime, timedelta
import mimetypes


class S3Uploader:
    """Upload charts and reports to S3 for storage and access."""
    
    def __init__(
        self,
        bucket_name: str,
        region: str = 'us-east-1',
        profile_name: Optional[str] = None
    ):
        """
        Initialize S3 uploader.
        
        Args:
            bucket_name: S3 bucket name
            region: AWS region
            profile_name: Optional AWS profile name
        """
        self.bucket_name = bucket_name
        self.region = region
        
        # Initialize S3 client
        session_kwargs = {}
        if profile_name:
            session_kwargs['profile_name'] = profile_name
        
        session = boto3.Session(**session_kwargs)
        self.s3_client = session.client('s3', region_name=region)
    
    def upload_file(
        self,
        file_path: str,
        s3_key: Optional[str] = None,
        acl: str = 'private',
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Upload a file to S3.
        
        Args:
            file_path: Local file path
            s3_key: S3 object key (defaults to filename)
            acl: Access control list ('private', 'public-read', etc.)
            metadata: Optional metadata dictionary
        
        Returns:
            Dictionary with upload details (bucket, key, url)
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ClientError: If upload fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Use filename as key if not provided
        if s3_key is None:
            s3_key = os.path.basename(file_path)
        
        # Guess content type
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'
        
        # Prepare extra args
        extra_args = {
            'ACL': acl,
            'ContentType': content_type
        }
        
        if metadata:
            extra_args['Metadata'] = metadata
        
        try:
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            
            # Construct S3 URL
            url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            return {
                'bucket': self.bucket_name,
                'key': s3_key,
                'url': url,
                'content_type': content_type
            }
        
        except ClientError as e:
            raise Exception(f"Failed to upload file to S3: {str(e)}")
    
    def upload_string(
        self,
        content: str,
        s3_key: str,
        content_type: str = 'text/plain',
        acl: str = 'private',
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Upload string content directly to S3.
        
        Args:
            content: String content to upload
            s3_key: S3 object key
            content_type: MIME type of content
            acl: Access control list
            metadata: Optional metadata dictionary
        
        Returns:
            Dictionary with upload details
        
        Raises:
            ClientError: If upload fails
        """
        extra_args = {
            'ACL': acl,
            'ContentType': content_type
        }
        
        if metadata:
            extra_args['Metadata'] = metadata
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content.encode('utf-8'),
                **extra_args
            )
            
            url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            return {
                'bucket': self.bucket_name,
                'key': s3_key,
                'url': url,
                'content_type': content_type
            }
        
        except ClientError as e:
            raise Exception(f"Failed to upload content to S3: {str(e)}")
    
    def generate_presigned_url(
        self,
        s3_key: str,
        expiration: int = 3600,
        http_method: str = 'get_object'
    ) -> str:
        """
        Generate a presigned URL for accessing an S3 object.
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
            http_method: HTTP method ('get_object', 'put_object')
        
        Returns:
            Presigned URL string
        
        Raises:
            ClientError: If URL generation fails
        """
        try:
            url = self.s3_client.generate_presigned_url(
                http_method,
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        
        except ClientError as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}")
    
    def upload_chart_html(
        self,
        html_content: str,
        user_id: str,
        chart_type: str,
        timestamp: Optional[datetime] = None
    ) -> dict:
        """
        Upload HTML chart with organized naming.
        
        Args:
            html_content: HTML content
            user_id: User identifier
            chart_type: Type of chart (e.g., 'cash_flow', 'categories')
            timestamp: Optional timestamp (defaults to now)
        
        Returns:
            Dictionary with upload details and presigned URL
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Create organized S3 key
        date_str = timestamp.strftime('%Y/%m/%d')
        time_str = timestamp.strftime('%H%M%S')
        s3_key = f"analytics/{user_id}/{date_str}/{chart_type}_{time_str}.html"
        
        # Upload file
        result = self.upload_string(
            content=html_content,
            s3_key=s3_key,
            content_type='text/html',
            metadata={
                'user_id': user_id,
                'chart_type': chart_type,
                'generated_at': timestamp.isoformat()
            }
        )
        
        # Generate presigned URL (expires in 7 days)
        presigned_url = self.generate_presigned_url(s3_key, expiration=604800)
        result['presigned_url'] = presigned_url
        
        return result
    
    def upload_report(
        self,
        html_content: str,
        user_id: str,
        report_type: str,
        timestamp: Optional[datetime] = None
    ) -> dict:
        """
        Upload HTML report with organized naming.
        
        Args:
            html_content: HTML report content
            user_id: User identifier
            report_type: Type of report
            timestamp: Optional timestamp (defaults to now)
        
        Returns:
            Dictionary with upload details and presigned URL
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Create organized S3 key
        date_str = timestamp.strftime('%Y/%m/%d')
        time_str = timestamp.strftime('%H%M%S')
        s3_key = f"reports/{user_id}/{date_str}/{report_type}_report_{time_str}.html"
        
        # Upload file
        result = self.upload_string(
            content=html_content,
            s3_key=s3_key,
            content_type='text/html',
            metadata={
                'user_id': user_id,
                'report_type': report_type,
                'generated_at': timestamp.isoformat()
            }
        )
        
        # Generate presigned URL (expires in 30 days)
        presigned_url = self.generate_presigned_url(s3_key, expiration=2592000)
        result['presigned_url'] = presigned_url
        
        return result
    
    def list_user_reports(
        self,
        user_id: str,
        max_results: int = 100
    ) -> list:
        """
        List reports for a specific user.
        
        Args:
            user_id: User identifier
            max_results: Maximum number of results
        
        Returns:
            List of report objects
        """
        prefix = f"reports/{user_id}/"
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_results
            )
            
            if 'Contents' not in response:
                return []
            
            reports = []
            for obj in response['Contents']:
                reports.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'url': f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{obj['Key']}"
                })
            
            return reports
        
        except ClientError as e:
            raise Exception(f"Failed to list reports: {str(e)}")
    
    def delete_object(self, s3_key: str) -> bool:
        """
        Delete an object from S3.
        
        Args:
            s3_key: S3 object key
        
        Returns:
            True if successful
        
        Raises:
            ClientError: If deletion fails
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        
        except ClientError as e:
            raise Exception(f"Failed to delete object: {str(e)}")
    
    def check_bucket_exists(self) -> bool:
        """
        Check if the S3 bucket exists.
        
        Returns:
            True if bucket exists, False otherwise
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError:
            return False
