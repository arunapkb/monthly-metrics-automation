"""
Google Drive service module.
Handles Drive authentication, file uploads, and folder operations.
"""
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from config.settings import settings


class GoogleDriveService:
    """Google Drive service for file operations."""

    def __init__(self):
        """Initialize Google Drive service."""
        self.service = None
        self.credentials = None

    def authenticate(self):
        """
        Handle Google Drive authentication and return service.

        Returns:
            googleapiclient.discovery.Resource: Authenticated Drive service
        """
        try:
            print("🔐 Authenticating with Google Drive...")

            self.credentials = self._get_credentials()
            self.service = build("drive", "v3", credentials=self.credentials)

            print("Success: Google Drive authentication successful")
            return self.service

        except Exception as e:
            print(f"Google Drive authentication failed: {e}")
            raise

    def _get_credentials(self):
        """Get or refresh Google credentials."""
        creds = None

        # Load existing token
        if settings.TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(str(settings.TOKEN_FILE), settings.GOOGLE_SCOPES)

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Refreshing Google credentials...")
                creds.refresh(Request())
            else:
                if not settings.CREDENTIALS_FILE.exists():
                    raise FileNotFoundError(f"Google credentials file not found: {settings.CREDENTIALS_FILE}\n"
                                            "Please download it from Google Cloud Console")

                print("🆕 Getting new Google credentials...")
                flow = InstalledAppFlow.from_client_secrets_file(str(settings.CREDENTIALS_FILE), settings.GOOGLE_SCOPES)
                creds = flow.run_local_server(port=0)

            # Save credentials
            with open(settings.TOKEN_FILE, "w") as token:
                token.write(creds.to_json())
            print("Success: Credentials saved")

        return creds

    def get_service(self):
        """
        Get authenticated Drive service (authenticate if needed).

        Returns:
            googleapiclient.discovery.Resource: Drive service
        """
        if not self.service:
            self.authenticate()
        return self.service

    def upload_file_to_folder(self, local_file_path, folder_id, new_filename=None):
        """
        Upload a file to a specific Google Drive folder.

        Args:
            local_file_path: Path to local file
            folder_id: Google Drive folder ID
            new_filename: Optional new name for the file

        Returns:
            dict: File information with ID and web view link
        """
        try:
            service = self.get_service()
            local_file_path = Path(local_file_path)

            if not local_file_path.exists():
                raise FileNotFoundError(f"Local file not found: {local_file_path}")

            # Verify folder exists
            self._verify_folder_exists(folder_id)

            # Prepare file metadata
            filename = new_filename or local_file_path.name
            file_metadata = {"name": filename, "parents": [folder_id]}

            print(f"📤 Uploading '{local_file_path.name}' as '{filename}'...")

            # Create media upload
            media = MediaFileUpload(str(local_file_path))

            # Upload file
            uploaded_file = service.files().create(body=file_metadata, media_body=media,
                fields="id, name, webViewLink").execute()

            print(f"Finished File upload successfully!")
            print(f"   File Name: {uploaded_file.get('name')}")
            print(f"   File ID: {uploaded_file.get('id')}")
            print(f"   Link: {uploaded_file.get('webViewLink')}")

            return uploaded_file

        except HttpError as error:
            if error.resp.status == 404:
                raise Exception(f"Folder with ID '{folder_id}' not found or not accessible")
            else:
                raise Exception(f"Google Drive API error: {error}")
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            raise

    def _verify_folder_exists(self, folder_id):
        """
        Verify that a folder exists and is accessible.

        Args:
            folder_id: Google Drive folder ID

        Returns:
            dict: Folder information
        """
        try:
            service = self.get_service()
            folder = service.files().get(fileId=folder_id, fields='name, id').execute()
            print(f"Success: Verified destination folder: '{folder.get('name')}' (ID: {folder_id})")
            return folder
        except HttpError as error:
            if error.resp.status == 404:
                raise Exception(f"Folder with ID '{folder_id}' not found or not accessible")
            raise

    def create_folder(self, folder_name, parent_folder_id=None):
        """
        Create a new folder in Google Drive.

        Args:
            folder_name: Name for the new folder
            parent_folder_id: Parent folder ID (None for root)

        Returns:
            dict: Created folder information
        """
        try:
            service = self.get_service()

            folder_metadata = {"name": folder_name, "mimeType": "application/vnd.google-apps.folder"}

            if parent_folder_id:
                folder_metadata["parents"] = [parent_folder_id]

            folder = service.files().create(body=folder_metadata, fields="id, name, webViewLink").execute()

            print(f"Success: Folder '{folder_name}' created with ID: {folder.get('id')}")
            return folder

        except Exception as e:
            print(f"❌ Failed to create folder: {e}")
            raise

    def find_folder_by_name(self, folder_name, parent_folder_id=None):
        """
        Find a folder by name.

        Args:
            folder_name: Name of folder to find
            parent_folder_id: Parent folder to search in (None for all)

        Returns:
            dict: Folder information or None if not found
        """
        try:
            service = self.get_service()

            query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"

            response = service.files().list(q=query, spaces='drive', fields='files(id, name, webViewLink)').execute()

            files = response.get('files', [])

            if files:
                folder = files[0]  # Return first match
                print(f"Success: Found folder '{folder_name}': {folder.get('id')}")
                return folder
            else:
                print(f"📁 Folder '{folder_name}' not found")
                return None

        except Exception as e:
            print(f"❌ Error searching for folder: {e}")
            return None

    def list_files_in_folder(self, folder_id, max_results=100):
        """
        List files in a specific folder.

        Args:
            folder_id: Google Drive folder ID
            max_results: Maximum number of files to return

        Returns:
            list: List of file information dictionaries
        """
        try:
            service = self.get_service()

            query = f"'{folder_id}' in parents and trashed=false"

            response = service.files().list(q=query, pageSize=max_results,
                fields='files(id, name, mimeType, createdTime, modifiedTime, size)').execute()

            files = response.get('files', [])
            print(f"Success: Found {len(files)} files in folder")

            return files

        except Exception as e:
            print(f"❌ Error listing files: {e}")
            return []

    def delete_file(self, file_id):
        """
        Delete a file from Google Drive.

        Args:
            file_id: Google Drive file ID

        Returns:
            bool: True if successful
        """
        try:
            service = self.get_service()
            service.files().delete(fileId=file_id).execute()
            print(f"Success: File deleted: {file_id}")
            return True
        except Exception as e:
            print(f"❌ Error deleting file: {e}")
            return False

    def find_spreadsheet_by_name(self, name, parent_id=None):
        """Find a Google Sheet file by name in a parent folder."""
        query = f"name='{name}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        results = self.get_service().files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        files = results.get('files', [])
        return files[0]['id'] if files else None

    def copy_file(self, file_id, new_name, dest_folder_id):
        """Copy a Google Drive file to a new location with a new name."""
        body = {'name': new_name, 'parents': [dest_folder_id]}
        return self.get_service().files().copy(fileId=file_id, body=body, fields='id, webViewLink').execute()

    def find_latest_spreadsheet_by_prefix(self, prefix, parent_id=None):
        """
        Find the latest Google Sheet in a folder whose name starts with the given prefix.
        Args:
            prefix (str): The prefix the spreadsheet name should start with.
            parent_id (str): The Drive folder ID to search in, or None for whole Drive.
        Returns:
            file_id (str) or None, file_name (str) or None
        """
        query = (f"name contains '{prefix}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false")
        if parent_id:
            query += f" and '{parent_id}' in parents"
        results = self.get_service().files().list(q=query, spaces='drive',
            fields='files(id, name, createdTime, modifiedTime)', orderBy='modifiedTime desc'  # Newest first
        ).execute()
        files = results.get('files', [])
        if not files:
            print(f"No spreadsheets starting with '{prefix}' found in specified folder.")
            return None, None
        # Return latest match
        return files[0]['id'], files[0]['name']
