import logging
from appwrite.client import Client
from appwrite.services.storage import Storage
from appwrite.id import ID
from appwrite.input_file import InputFile
from flask import current_app

logger = logging.getLogger(__name__)

def init_appwrite():
    """Initialize Appwrite client"""
    try:
        logger.debug("Initializing Appwrite client...")
        client = Client()
        client.set_endpoint(current_app.config['APPWRITE_ENDPOINT'])
        client.set_project(current_app.config['APPWRITE_PROJECT_ID'])
        client.set_key(current_app.config['APPWRITE_API_KEY'])

        storage = Storage(client)
        logger.info("Appwrite client initialized successfully")
        return storage
    except Exception as e:
        logger.error(f"Failed to initialize Appwrite client: {str(e)}")
        raise

def upload_file(file_bytes, filename):
    """Upload a file to Appwrite storage
    
    Args:
        file_bytes: The file data as bytes
        filename: Original filename for reference
        
    Returns:
        str: The file ID if successful, None if failed
    """
    try:
        logger.debug(f"Starting file upload process for filename: {filename}")
        storage = init_appwrite()
        
        # Generate a valid file ID
        file_id = ID.unique()
        logger.debug(f"Generated file ID: {file_id}")
        
        # Create input file with original filename
        input_file = InputFile.from_bytes(file_bytes, filename)
        logger.debug("Created InputFile object")
        
        result = storage.create_file(
            bucket_id=current_app.config['APPWRITE_BUCKET_ID'],
            file_id=file_id,
            file=input_file,
            permissions=['read("any")']
        )
        logger.info(f"Successfully uploaded file. ID: {result['$id']}")
        return result['$id']
    except Exception as e:
        logger.error(f"Error uploading file {filename}: {str(e)}", exc_info=True)
        return None

def delete_file(file_id):
    """Delete a file from Appwrite storage"""
    try:
        storage = init_appwrite()
        storage.delete_file(
            bucket_id=current_app.config['APPWRITE_BUCKET_ID'],
            file_id=file_id
        )
        return True
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return False 