import os
import uuid
import logging
from flask import current_app
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

def get_upload_path():
    """Get the upload directory path, ensure it exists"""
    # Check if we're using local or NAS storage
    if current_app.config.get('USE_NAS_STORAGE', False):
        upload_folder = current_app.config['NAS_UPLOAD_FOLDER']
        logger.debug(f"Using NAS storage path: {upload_folder}")
    else:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        logger.debug(f"Using local storage path: {upload_folder}")
        
    if not os.path.exists(upload_folder):
        try:
            logger.debug(f"Creating upload directory: {upload_folder}")
            os.makedirs(upload_folder)
        except Exception as e:
            logger.error(f"Failed to create upload directory: {str(e)}")
            # Fallback to local if NAS fails
            if current_app.config.get('USE_NAS_STORAGE', False):
                logger.warning("Falling back to local storage")
                upload_folder = current_app.config['UPLOAD_FOLDER']
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
    
    return upload_folder

def upload_file(file_bytes, filename):
    """Upload a file to local storage
    
    Args:
        file_bytes: The file data as bytes
        filename: Original filename for reference
        
    Returns:
        str: The file ID if successful, None if failed
    """
    try:
        logger.debug(f"Starting file upload process for filename: {filename}")
        
        # Generate a unique file ID
        file_id = str(uuid.uuid4())
        logger.debug(f"Generated file ID: {file_id}")
        
        # Secure the filename
        secure_name = secure_filename(filename)
        
        # Create a unique filename with the original extension
        _, file_extension = os.path.splitext(secure_name)
        storage_filename = f"{file_id}{file_extension}"
        
        # Get upload path
        upload_path = get_upload_path()
        file_path = os.path.join(upload_path, storage_filename)
        
        # Save the file
        with open(file_path, 'wb') as f:
            f.write(file_bytes)
        
        logger.info(f"Successfully uploaded file. ID: {file_id}")
        return file_id
    except Exception as e:
        logger.error(f"Error uploading file {filename}: {str(e)}", exc_info=True)
        return None

def delete_file(file_id):
    """Delete a file from local storage"""
    try:
        # First find all files that start with the file_id
        upload_path = get_upload_path()
        
        # Look for any file that starts with the file_id (could have different extensions)
        for filename in os.listdir(upload_path):
            if filename.startswith(file_id):
                file_path = os.path.join(upload_path, filename)
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
                return True
        
        logger.warning(f"No file found with ID: {file_id}")
        return False
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return False 