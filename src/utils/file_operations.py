"""
File operations utilities.
Handles file finding, renaming, and download management.
"""
import os
import time
from datetime import datetime
from pathlib import Path

class FileOperations:
    """Utility class for file operations."""

    @staticmethod
    def find_latest_file(folder_path):
        """
        Find the most recently modified file in a directory.

        Args:
            folder_path: Path to search for files

        Returns:
            Path: Path to the latest file, or None if no files found
        """
        folder_path = Path(folder_path)

        if not folder_path.exists() or not folder_path.is_dir():
            print(f"ERROR: The folder '{folder_path}' does not exist or is not a directory.")
            return None

        # Get all files (not directories)
        files = [f for f in folder_path.iterdir() if f.is_file()]

        # Filter out temporary download files
        files = [f for f in files if not f.name.endswith('.crdownload')]

        if not files:
            print(f"ERROR: No files found in '{folder_path}'.")
            return None

        # Find the file with the latest modification time
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        print(f"Success: Found latest file: {latest_file.name}")
        return latest_file

    @staticmethod
    def find_and_rename_latest_file(download_dir, new_name_prefix, wait_seconds=15):
        """
        Wait for download, find the newest file, and rename it with timestamp.

        Args:
            download_dir: Directory to search for files
            new_name_prefix: Prefix for the new filename
            wait_seconds: Time to wait for download completion

        Returns:
            Path: Path to the renamed file, or None if failed
        """
        print(f"⏳ Waiting {wait_seconds} seconds for download to complete...")
        time.sleep(wait_seconds)

        try:
            # Find the latest file
            latest_file = FileOperations.find_latest_file(download_dir)

            if not latest_file:
                print("ERROR: No downloaded file found.")
                return None

            # Create new filename with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_extension = latest_file.suffix
            new_filename = f"{new_name_prefix}_{timestamp}{file_extension}"
            new_filepath = latest_file.parent / new_filename

            # Rename the file
            latest_file.rename(new_filepath)
            print(f"Success: File successfully renamed to: {new_filename}")

            return new_filepath

        except Exception as e:
            print(f"ERROR:An error occurred during file renaming: {e}")
            return None

    @staticmethod
    def ensure_directory_exists(directory_path):
        """
        Ensure a directory exists, create if it doesn't.

        Args:
            directory_path: Path to the directory

        Returns:
            Path: Path object for the directory
        """
        directory_path = Path(directory_path)
        directory_path.mkdir(parents=True, exist_ok=True)
        return directory_path

    @staticmethod
    def clean_old_files(directory_path, max_age_days=7, pattern="*"):
        """
        Clean old files from a directory.

        Args:
            directory_path: Directory to clean
            max_age_days: Maximum age of files to keep
            pattern: File pattern to match (e.g., "*.csv")

        Returns:
            int: Number of files deleted
        """
        directory_path = Path(directory_path)

        if not directory_path.exists():
            return 0

        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        deleted_count = 0

        try:
            for file_path in directory_path.glob(pattern):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        deleted_count += 1
                        print(f"🗑️ Deleted old file: {file_path.name}")

            if deleted_count > 0:
                print(f"Success: Cleaned {deleted_count} old files from {directory_path}")

            return deleted_count

        except Exception as e:
            print(f"⚠️ Error during file cleanup: {e}")
            return 0

    @staticmethod
    def get_file_info(file_path):
        """
        Get detailed information about a file.

        Args:
            file_path: Path to the file

        Returns:
            dict: File information including size, dates, etc.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return None

        stat = file_path.stat()

        return {
            'name': file_path.name,
            'size_bytes': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'created': datetime.fromtimestamp(stat.st_ctime),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'extension': file_path.suffix,
            'absolute_path': file_path.absolute()
        }

    @staticmethod
    def wait_for_file_stable(file_path, stable_duration=2, max_wait=30):
        """
        Wait for a file to stop changing (useful for downloads).

        Args:
            file_path: Path to monitor
            stable_duration: Seconds file must be stable
            max_wait: Maximum time to wait

        Returns:
            bool: True if file became stable, False if timeout
        """
        file_path = Path(file_path)
        start_time = time.time()
        last_size = 0
        stable_start = None

        while time.time() - start_time < max_wait:
            if file_path.exists():
                current_size = file_path.stat().st_size

                if current_size == last_size and current_size > 0:
                    if stable_start is None:
                        stable_start = time.time()
                    elif time.time() - stable_start >= stable_duration:
                        print(f"Success: File {file_path.name} is stable ({current_size} bytes)")
                        return True
                else:
                    stable_start = None
                    last_size = current_size

            time.sleep(0.5)

        print(f"⏰ Timeout waiting for file {file_path.name} to stabilize")
        return False

    @staticmethod
    def backup_file(file_path, backup_dir=None):
        """
        Create a backup copy of a file.

        Args:
            file_path: Path to the file to backup
            backup_dir: Directory for backup (creates 'backups' subdir if None)

        Returns:
            Path: Path to the backup file
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if backup_dir is None:
            backup_dir = file_path.parent / "backups"
        else:
            backup_dir = Path(backup_dir)

        FileOperations.ensure_directory_exists(backup_dir)

        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = backup_dir / backup_name

        # Copy file
        import shutil
        shutil.copy2(file_path, backup_path)

        print(f"Success: Backup created: {backup_path}")
        return backup_path
