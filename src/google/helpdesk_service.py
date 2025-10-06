class HelpdeskCallsService:
    def __init__(self, drive_service, sheets_service, logger=None):
        self.drive_service = drive_service
        self.sheets_service = sheets_service
        self.logger = logger

    def ensure_google_sheet(self, file_id, new_name, dest_folder_id):
        """
        If the file is a Google Sheet, return it; otherwise, convert Excel to Google Sheet.
        """
        # Try to get file metadata to check MIME type
        file = self.drive_service.get_service().files().get(
            fileId=file_id,
            fields="id, mimeType"
        ).execute()
        if file.get('mimeType') == "application/vnd.google-apps.spreadsheet":
            if self.logger:
                self.logger.info("Helpdesk file is already a Google Sheet.")
            return file_id
        # Otherwise, convert
        if self.logger:
            self.logger.info("Helpdesk file is Excel; converting to Google Sheet...")
        converted = self.drive_service.convert_excel_to_google_sheet(file_id, new_name, dest_folder_id)
        return converted['id']

    def get_helpdesk_calls_count(self, spreadsheet_id, sheet_name, count_func=None):
        data = self.sheets_service.get_sheet_data(spreadsheet_id, sheet_name)
        if count_func:
            return count_func(data)
        return self.sheets_service.count_rows(data)
