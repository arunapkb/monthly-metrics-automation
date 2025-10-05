"""
Google Sheets service module.
Handles CSV to Sheets conversion and sheet operations.
"""
import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from src.google.drive_service import GoogleDriveService

class GoogleSheetsService:
    """Google Sheets service for spreadsheet operations."""

    def __init__(self, drive_service=None):
        """
        Initialize Google Sheets service.

        Args:
            drive_service: Optional GoogleDriveService instance
        """
        self.drive_service = drive_service or GoogleDriveService()
        self.sheets_service = None

    def get_sheets_service(self):
        """
        Get authenticated Sheets service.

        Returns:
            googleapiclient.discovery.Resource: Sheets service
        """
        if not self.sheets_service:
            credentials = self.drive_service._get_credentials()
            self.sheets_service = build("sheets", "v4", credentials=credentials)
        return self.sheets_service

    def upload_csv_as_google_sheet(self, local_csv_path, folder_id, sheet_name):
        """
        Upload CSV file and convert to Google Sheet with renamed first tab.

        Args:
            local_csv_path: Path to local CSV file
            folder_id: Google Drive folder ID
            sheet_name: Name for the new Google Sheet

        Returns:
            dict: Created spreadsheet information
        """
        try:
            print(f"Converting CSV to Google Sheet: '{sheet_name}'...")

            # Get services
            drive_service = self.drive_service.get_service()
            sheets_service = self.get_sheets_service()

            # Upload and convert CSV to Google Sheet
            spreadsheet_info = self._upload_and_convert_csv(
                drive_service, local_csv_path, folder_id, sheet_name
            )

            spreadsheet_id = spreadsheet_info.get('id')

            # Wait for sheet to be ready
            print("⏳ Waiting for sheet to be fully processed...")
            time.sleep(5)

            # Rename first sheet to 'Summary'
            self._rename_first_sheet(sheets_service, spreadsheet_id, 'Summary')

            print(f" CSV conversion completed successfully!")
            print(f"   Sheet Name: '{spreadsheet_info.get('name')}'")
            print(f"   Sheet ID: {spreadsheet_id}")
            print(f"   Link: {spreadsheet_info.get('webViewLink')}")

            return spreadsheet_info

        except Exception as e:
            print(f"ERROR:CSV to Sheets conversion failed: {e}")
            raise

    def _upload_and_convert_csv(self, drive_service, local_csv_path, folder_id, sheet_name):
        """Upload CSV and convert to Google Sheet."""
        file_metadata = {
            "name": sheet_name,
            "parents": [folder_id],
            "mimeType": "application/vnd.google-apps.spreadsheet"
        }

        media = MediaFileUpload(
            local_csv_path, 
            mimetype='text/csv', 
            resumable=True
        )

        uploaded_sheet = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, name, webViewLink"
        ).execute()

        print(f"Success: CSV uploaded and converted to Google Sheet")
        return uploaded_sheet

    def _rename_first_sheet(self, sheets_service, spreadsheet_id, new_name):
        """Rename the first sheet in a spreadsheet."""
        try:
            print(f"🏷️ Renaming first sheet to '{new_name}'...")

            # Get spreadsheet metadata to find first sheet ID
            spreadsheet_metadata = sheets_service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()

            sheets = spreadsheet_metadata.get('sheets', [])

            if not sheets:
                raise Exception("No sheets found in the spreadsheet")

            # Get the first sheet's ID
            first_sheet_id = sheets[0].get('properties', {}).get('sheetId')

            if first_sheet_id is None:
                raise Exception("Could not find first sheet ID")

            print(f"Success: Found first sheet with ID: {first_sheet_id}")

            # Prepare rename request
            rename_request = {
                'requests': [{
                    'updateSheetProperties': {
                        'properties': {
                            'sheetId': first_sheet_id,
                            'title': new_name
                        },
                        'fields': 'title'
                    }
                }]
            }

            # Execute rename
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=rename_request
            ).execute()

            print(f"Success: First sheet renamed to '{new_name}'")

        except HttpError as error:
            print(f"Error renaming sheet: {error}")
            print(f"   Error details: {error.content}")
            raise
        except Exception as e:
            print(f"Unexpected error renaming sheet: {e}")
            raise

    def create_new_sheet(self, spreadsheet_id, sheet_name):
        """
        Add a new sheet to an existing spreadsheet.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name for the new sheet

        Returns:
            dict: New sheet information
        """
        try:
            sheets_service = self.get_sheets_service()

            request_body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }]
            }

            response = sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=request_body
            ).execute()

            new_sheet = response['replies'][0]['addSheet']['properties']
            print(f"Success: New sheet '{sheet_name}' created with ID: {new_sheet['sheetId']}")

            return new_sheet

        except Exception as e:
            print(f"Error creating new sheet: {e}")
            raise

    def write_data_to_sheet(self, spreadsheet_id, sheet_name, data, start_cell='A1'):
        """
        Write data to a specific sheet.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the sheet to write to
            data: 2D list of data to write
            start_cell: Starting cell (default: 'A1')

        Returns:
            dict: Update response
        """
        try:
            sheets_service = self.get_sheets_service()

            range_name = f"'{sheet_name}'!{start_cell}"

            value_input_option = 'RAW'  # or 'USER_ENTERED'

            body = {
                'values': data
            }

            result = sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body
            ).execute()

            updated_cells = result.get('updatedCells', 0)
            print(f"Success: Updated {updated_cells} cells in '{sheet_name}'")

            return result

        except Exception as e:
            print(f"Error writing data to sheet: {e}")
            raise

    def read_data_from_sheet(self, spreadsheet_id, sheet_name, cell_range='A:Z'):
        """
        Read data from a specific sheet.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the sheet to read from
            cell_range: Range to read (default: 'A:Z')

        Returns:
            list: 2D list of cell values
        """
        try:
            sheets_service = self.get_sheets_service()

            range_name = f"'{sheet_name}'!{cell_range}"

            result = sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()

            values = result.get('values', [])
            print(f"Success: Read {len(values)} rows from '{sheet_name}'")

            return values

        except Exception as e:
            print(f"Error reading data from sheet: {e}")
            raise

    def format_sheet_header(self, spreadsheet_id, sheet_name, header_row=1):
        """
        Apply formatting to header row (bold, background color).

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the sheet
            header_row: Row number to format (1-based, default: 1)

        Returns:
            dict: Format response
        """
        try:
            sheets_service = self.get_sheets_service()

            # Get sheet ID by name
            sheet_id = self._get_sheet_id_by_name(spreadsheet_id, sheet_name)

            request_body = {
                'requests': [{
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet_id,
                            'startRowIndex': header_row - 1,
                            'endRowIndex': header_row
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'bold': True
                                },
                                'backgroundColor': {
                                    'red': 0.9,
                                    'green': 0.9,
                                    'blue': 0.9
                                }
                            }
                        },
                        'fields': 'userEnteredFormat(textFormat,backgroundColor)'
                    }
                }]
            }

            response = sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=request_body
            ).execute()

            print(f"Success: Header formatting applied to '{sheet_name}'")
            return response

        except Exception as e:
            print(f"Error formatting header: {e}")
            raise

    def _get_sheet_id_by_name(self, spreadsheet_id, sheet_name):
        """Get sheet ID by sheet name."""
        sheets_service = self.get_sheets_service()

        spreadsheet = sheets_service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()

        for sheet in spreadsheet.get('sheets', []):
            if sheet['properties']['title'] == sheet_name:
                return sheet['properties']['sheetId']

        raise Exception(f"Sheet '{sheet_name}' not found")

    def get_sheet_data(self, spreadsheet_id, sheet_name):
        """Read all data from a specific sheet."""
        return self.get_sheets_service().spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}"
        ).execute().get('values', [])

    def count_rows_and_bugs(self, data):
        """Count rows (excluding header) and how many first column values start with 'BUG'."""
        if not data or len(data) < 2:
            return 0, 0  # no data or only header
        rows = data[1:]  # exclude header
        bug_count = sum(1 for row in rows if row and row[0].startswith("BUG"))
        return len(rows), bug_count

    def update_sheet_cell(self, spreadsheet_id, sheet_name, cell, value):
        """Update a specific cell in the sheet."""
        body = {"values": [[value]]}
        return self.get_sheets_service().spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=f"{sheet_name}!{cell}",
            valueInputOption="RAW", body=body
        ).execute()