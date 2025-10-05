#!/usr/bin/env python3
"""
Jira Automation Main Script
Orchestrates the complete workflow: JumpCloud login -> Jira export -> Google Sheets upload
"""
import logging
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from src.automation.web_driver import WebDriverManager
from src.auth.jumpcloud_auth import JumpCloudAuth
from src.jira.operations import JiraOperations
from src.google.drive_service import GoogleDriveService
from src.google.sheets_service import GoogleSheetsService
from src.utils.file_operations import FileOperations


class JiraAutomationWorkflow:
    """Main workflow orchestrator for Jira automation."""

    def __init__(self):
        """Initialize the automation workflow."""
        self.driver_manager = WebDriverManager()
        self.driver = None
        self.file_ops = FileOperations()

        # Setup logging
        self._setup_logging()

        # Validate configuration
        self._validate_configuration()

    def _setup_logging(self):
        """Setup logging configuration."""
        log_file = settings.LOGS_FOLDER / "jira_automation.log"

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                            handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)])

        self.logger = logging.getLogger(__name__)

    def _validate_configuration(self):
        """Validate that all required configuration is available."""
        try:
            settings.validate_credentials()
            self.logger.info("Success: Configuration validation passed")
        except ValueError as e:
            self.logger.error(f"ERROR:Configuration validation failed: {e}")
            raise

    def run_full_workflow(self):
        """Execute the complete automation workflow."""
        try:
            self.logger.info("Starting: Starting Jira Automation Workflow")

            # Step 1: Setup WebDriver
            self.driver = self._setup_webdriver()

            # Step 2: Authenticate with JumpCloud
            self._authenticate_jumpcloud()

            # Step 3: Navigate to Jira and export data
            exported_file = self._export_jira_data()

            # Step 4: Upload to Google Sheets
            self._upload_to_google_sheets(exported_file)

            # Step 5: Copy Final monthly metrics and update it with generated jira google sheets.
            self.read_jira_report_and_update_count_to_monthly_metrics()
            self.logger.info("Workflow completed successfully!")
            return True

        except Exception as e:
            self.logger.error(f"ERROR:Workflow failed: {e}")
            return False
        finally:
            self._cleanup()

    def _setup_webdriver(self):
        """Setup and return WebDriver instance."""
        self.logger.info("Setting up WebDriver...")
        return self.driver_manager.setup_driver()

    def _authenticate_jumpcloud(self):
        """Authenticate with JumpCloud."""
        self.logger.info("Authenticating with JumpCloud...")

        auth = JumpCloudAuth(self.driver)

        if not auth.login():
            raise Exception("JumpCloud authentication failed")

        # Navigate to Jira
        auth.navigate_to_jira()
        self.logger.info("Success: JumpCloud authentication and Jira navigation completed")

    def _export_jira_data(self):
        """Export data from Jira using JQL query."""
        self.logger.info("Exporting Jira data...")

        jira_ops = JiraOperations(self.driver)

        exported_file = jira_ops.execute_jql_and_export(jira_url=settings.JIRA_SEARCH_URL, jql_query=settings.JQL_QUERY)

        if not exported_file or not exported_file.exists():
            raise Exception("Jira export failed - no file was created")

        self.logger.info(f"Success: Jira data exported to: {exported_file}")
        return exported_file

    def _upload_to_google_sheets(self, csv_file_path):
        """Upload CSV file to Google Sheets."""
        self.logger.info("Uploading to Google Sheets...")

        # Initialize Google services
        drive_service = GoogleDriveService()
        sheets_service = GoogleSheetsService(drive_service)

        # Create sheet name from file
        sheet_name = csv_file_path.stem  # filename without extension

        # Upload to downloads folder and convert to Google Sheet
        spreadsheet_info = sheets_service.upload_csv_as_google_sheet(local_csv_path=str(csv_file_path),
                                                                     folder_id=settings.DRIVE_FOLDER_ID,
                                                                     sheet_name=sheet_name)

        self.logger.info("Success: Google Sheets upload completed")
        return spreadsheet_info

    def _cleanup(self):
        """Cleanup resources."""
        if self.driver:
            self.logger.info("Cleaning up...")
            self.driver_manager.close_driver()

        # Optional: Clean old files
        try:
            deleted_count = self.file_ops.clean_old_files(directory_path=settings.DOWNLOADS_FOLDER, max_age_days=7,
                                                          pattern="*.csv")
            if deleted_count > 0:
                self.logger.info(f"🗑Cleaned {deleted_count} old CSV files")
        except Exception as e:
            self.logger.warning(f"⚠File cleanup failed: {e}")

    def run_jira_export_only(self):
        """Run only the Jira export part of the workflow."""
        try:
            self.logger.info("Running Jira export only...")

            self.driver = self._setup_webdriver()
            self._authenticate_jumpcloud()
            exported_file = self._export_jira_data()

            self.logger.info(f"Success: Jira export completed: {exported_file}")
            return exported_file

        except Exception as e:
            self.logger.error(f"Jira export failed: {e}")
            raise
        finally:
            self._cleanup()

    def run_upload_only(self, csv_file_path):
        """Run only the Google Sheets upload part."""
        try:
            self.logger.info("Running Google Sheets upload only...")

            csv_file_path = Path(csv_file_path)
            if not csv_file_path.exists():
                raise FileNotFoundError(f"CSV file not found: {csv_file_path}")

            spreadsheet_info = self._upload_to_google_sheets(csv_file_path)

            self.logger.info("Success: Upload completed")
            return spreadsheet_info

        except Exception as e:
            self.logger.error(f"ERROR:Upload failed: {e}")
            raise

    def read_jira_report_and_update_count_to_monthly_metrics(self):
        gd = GoogleDriveService()
        gs = GoogleSheetsService(gd)

        # 1. Find template folder and file by name
        template_folder_id = gd.find_folder_by_name("Automation_Monthly_Metrics_Pradeep").get('id')
        file_id = gd.find_spreadsheet_by_name("Test_TSA Monthly Metrics_Sep_2025", parent_id=template_folder_id)

        # 2. Copy the file to the destination folder (with new name)
        from datetime import datetime
        dest_folder_id = "1qrEWlZaEVCFxbyCcXLjxAkVFhr1jAbc8"
        current_month = datetime.now().strftime("%B_%Y")
        new_file_name = f"TSA Monthly Metrics_{current_month}"
        copied_file = gd.copy_file(file_id, new_file_name, dest_folder_id)

        # 3. Read 'Summary' sheet data from the copied file
        jira_report_spreadsheet_id, jira_report_spreadsheet_name = gd.find_latest_spreadsheet_by_prefix('Jira_Report_',
                                                                                                        parent_id=settings.DRIVE_FOLDER_ID)
        summary_data = gs.get_sheet_data(jira_report_spreadsheet_id, "Summary")

        # 4. Calculate required counts
        row_count, bug_count = gs.count_rows_and_bugs(summary_data)

        # (Optional: pick cell, e.g. D1, to update with these numbers)
        message = f"Rows: {row_count}, Bugs: {bug_count}"
        monthly_metrics_spreadsheet_id = copied_file['id']
        gs.update_sheet_cell(monthly_metrics_spreadsheet_id, "Summary", "B3", row_count)
        gs.update_sheet_cell(monthly_metrics_spreadsheet_id, "Summary", "B4", bug_count)

        print(f"Summary: {message}, Updated in {new_file_name} ({copied_file['webViewLink']})")


def main():
    """Main entry point for the application."""
    import argparse

    parser = argparse.ArgumentParser(description="Jira Automation Workflow")
    parser.add_argument('--mode', choices=['full', 'export-only', 'upload-only',
                                           'read_jira_report_and_update_count_to_monthly_metrics-only'], default='full',
                        help='Workflow mode (default: full)')
    parser.add_argument('--file', help='CSV file path for upload-only mode')

    args = parser.parse_args()

    # Initialize workflow
    workflow = JiraAutomationWorkflow()

    try:
        if args.mode == 'full':
            success = workflow.run_full_workflow()
        elif args.mode == 'export-only':
            workflow.run_jira_export_only()
            success = True
        elif args.mode == 'upload-only':
            if not args.file:
                print("ERROR:--file argument required for upload-only mode")
                sys.exit(1)
            workflow.run_upload_only(args.file)
            success = True
        elif args.mode == 'read_jira_report_and_update_count_to_monthly_metrics-only':
            workflow.read_jira_report_and_update_count_to_monthly_metrics()
            success = True

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR:Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
