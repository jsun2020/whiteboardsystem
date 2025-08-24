import os
import shutil
from typing import Optional
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from config import Config
import uuid
import mimetypes

# Optional AWS S3 support
try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

class StorageService:
    def __init__(self):
        self.storage_type = Config.STORAGE_TYPE
        self.upload_folder = Config.UPLOAD_FOLDER
        
        # Initialize S3 client if using S3 storage
        if self.storage_type == 's3':
            if not HAS_BOTO3:
                print("Warning: boto3 not available, falling back to local storage")
                self.storage_type = 'local'
            else:
                self.s3_client = boto3.client(
                    's3',
                    region_name=Config.S3_REGION,
                    aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY
                )
            self.bucket_name = Config.S3_BUCKET
        
        # Ensure upload folder exists for local storage
        if self.storage_type == 'local':
            try:
                os.makedirs(self.upload_folder, exist_ok=True)
            except OSError:
                # In serverless environments, directories will be created on demand
                pass
    
    def save_file(self, file: FileStorage, filename: str, subfolder: str = '') -> str:
        """
        Save file to storage (local or S3)
        Returns the path/URL where the file was saved
        """
        try:
            if self.storage_type == 'local':
                return self._save_local(file, filename, subfolder)
            elif self.storage_type == 's3':
                return self._save_s3(file, filename, subfolder)
            else:
                raise ValueError(f"Unsupported storage type: {self.storage_type}")
        
        except Exception as e:
            raise Exception(f"Failed to save file: {str(e)}")
    
    def _save_local(self, file: FileStorage, filename: str, subfolder: str) -> str:
        """
        Save file to local filesystem
        """
        # Create subfolder if specified
        save_directory = os.path.join(self.upload_folder, subfolder) if subfolder else self.upload_folder
        try:
            os.makedirs(save_directory, exist_ok=True)
        except OSError:
            # In serverless environments, directories will be created on demand
            pass
        
        # Create full file path
        file_path = os.path.join(save_directory, filename)
        
        # Save the file
        file.save(file_path)
        
        return file_path
    
    def _save_s3(self, file: FileStorage, filename: str, subfolder: str) -> str:
        """
        Save file to S3
        """
        # Create S3 key
        s3_key = f"{subfolder}/{filename}" if subfolder else filename
        
        # Get MIME type
        mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        
        # Upload to S3
        self.s3_client.upload_fileobj(
            file,
            self.bucket_name,
            s3_key,
            ExtraArgs={
                'ContentType': mime_type,
                'ServerSideEncryption': 'AES256'
            }
        )
        
        # Return S3 URL
        return f"s3://{self.bucket_name}/{s3_key}"
    
    def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """
        Get a URL to access the file (signed URL for S3, local path for local storage)
        """
        try:
            if self.storage_type == 'local':
                return file_path
            elif self.storage_type == 's3':
                # Extract S3 key from path
                if file_path.startswith('s3://'):
                    s3_key = file_path.replace(f"s3://{self.bucket_name}/", "")
                    
                    # Generate presigned URL
                    url = self.s3_client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': self.bucket_name, 'Key': s3_key},
                        ExpiresIn=expires_in
                    )
                    return url
            
            return file_path
        
        except Exception as e:
            print(f"Failed to get file URL: {e}")
            return file_path
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete file from storage
        """
        try:
            if self.storage_type == 'local':
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return True
                return False
            
            elif self.storage_type == 's3':
                if file_path.startswith('s3://'):
                    s3_key = file_path.replace(f"s3://{self.bucket_name}/", "")
                    self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
                    return True
            
            return False
        
        except Exception as e:
            print(f"Failed to delete file: {e}")
            return False
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists in storage
        """
        try:
            if self.storage_type == 'local':
                return os.path.exists(file_path)
            
            elif self.storage_type == 's3':
                if file_path.startswith('s3://'):
                    s3_key = file_path.replace(f"s3://{self.bucket_name}/", "")
                    try:
                        self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
                        return True
                    except:
                        return False
            
            return False
        
        except Exception:
            return False
    
    def get_file_info(self, file_path: str) -> Optional[dict]:
        """
        Get file information (size, modified date, etc.)
        """
        try:
            if self.storage_type == 'local':
                if os.path.exists(file_path):
                    stat = os.stat(file_path)
                    return {
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'path': file_path
                    }
            
            elif self.storage_type == 's3':
                if file_path.startswith('s3://'):
                    s3_key = file_path.replace(f"s3://{self.bucket_name}/", "")
                    try:
                        response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
                        return {
                            'size': response['ContentLength'],
                            'modified': response['LastModified'].timestamp(),
                            'path': file_path,
                            'etag': response['ETag']
                        }
                    except:
                        pass
            
            return None
        
        except Exception:
            return None
    
    def copy_file(self, source_path: str, dest_path: str) -> bool:
        """
        Copy file within storage
        """
        try:
            if self.storage_type == 'local':
                shutil.copy2(source_path, dest_path)
                return True
            
            elif self.storage_type == 's3':
                # Extract S3 keys
                if source_path.startswith('s3://') and dest_path.startswith('s3://'):
                    source_key = source_path.replace(f"s3://{self.bucket_name}/", "")
                    dest_key = dest_path.replace(f"s3://{self.bucket_name}/", "")
                    
                    # Copy in S3
                    self.s3_client.copy_object(
                        Bucket=self.bucket_name,
                        CopySource={'Bucket': self.bucket_name, 'Key': source_key},
                        Key=dest_key
                    )
                    return True
            
            return False
        
        except Exception as e:
            print(f"Failed to copy file: {e}")
            return False
    
    def list_files(self, subfolder: str = '') -> list:
        """
        List files in a subfolder
        """
        try:
            files = []
            
            if self.storage_type == 'local':
                search_path = os.path.join(self.upload_folder, subfolder) if subfolder else self.upload_folder
                if os.path.exists(search_path):
                    for filename in os.listdir(search_path):
                        file_path = os.path.join(search_path, filename)
                        if os.path.isfile(file_path):
                            files.append({
                                'name': filename,
                                'path': file_path,
                                'size': os.path.getsize(file_path)
                            })
            
            elif self.storage_type == 's3':
                prefix = f"{subfolder}/" if subfolder else ""
                
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix
                )
                
                for obj in response.get('Contents', []):
                    files.append({
                        'name': os.path.basename(obj['Key']),
                        'path': f"s3://{self.bucket_name}/{obj['Key']}",
                        'size': obj['Size']
                    })
            
            return files
        
        except Exception as e:
            print(f"Failed to list files: {e}")
            return []
    
    def cleanup_old_files(self, subfolder: str = '', days_old: int = 30) -> int:
        """
        Clean up files older than specified days
        Returns number of files deleted
        """
        import time
        
        deleted_count = 0
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        
        try:
            if self.storage_type == 'local':
                search_path = os.path.join(self.upload_folder, subfolder) if subfolder else self.upload_folder
                if os.path.exists(search_path):
                    for filename in os.listdir(search_path):
                        file_path = os.path.join(search_path, filename)
                        if os.path.isfile(file_path):
                            if os.path.getmtime(file_path) < cutoff_time:
                                os.remove(file_path)
                                deleted_count += 1
            
            elif self.storage_type == 's3':
                prefix = f"{subfolder}/" if subfolder else ""
                
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix
                )
                
                for obj in response.get('Contents', []):
                    if obj['LastModified'].timestamp() < cutoff_time:
                        self.s3_client.delete_object(
                            Bucket=self.bucket_name,
                            Key=obj['Key']
                        )
                        deleted_count += 1
        
        except Exception as e:
            print(f"Cleanup failed: {e}")
        
        return deleted_count