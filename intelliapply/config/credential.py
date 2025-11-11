"""
Credential configuration module - loads from YAML config in user directory.
Manages configuration files with cross-platform support.
"""

import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path
from typing import Dict, Any
from urllib.parse import urlparse
import yaml

from intelliapply.utils.print_utils import print_


class ConfigManager:
    """Manages configuration files in user's home directory."""

    # Config directory name in user's home folder
    CONFIG_DIR_NAME = "intelliApply_config"
    CONFIG_FILE_NAME = "config.yaml"

    def __init__(self):
        """Initialize config manager and ensure config exists."""
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / self.CONFIG_FILE_NAME
        self._ensure_config_exists()
        self._ensure_config_valid()

    @staticmethod
    def _get_config_dir() -> Path:
        """
        Get the configuration directory path based on OS.

        Returns:
            Path to config directory in user's home folder
        """
        home = Path.home()
        config_dir = home / ConfigManager.CONFIG_DIR_NAME
        return config_dir

    def _get_template_path(self) -> Path:
        """
        Get path to the credential-example.yaml template.

        Returns:
            Path to template file
        """
        current_dir = Path(__file__).parent
        template_path = current_dir / "credential-example.yaml"
        return template_path

    def _ensure_config_exists(self) -> None:
        """
        Ensure config directory and file exist.
        If first time, copy template and prompt user to edit.
        """
        # Create config directory if it doesn't exist
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
            print_(f"Created config directory: {self.config_dir}", "GREEN")

        # Check if config file exists
        if not self.config_file.exists():
            self._create_config_from_template()
            self._open_config_file()
            print_("\n" + "=" * 60)
            print_("FIRST TIME SETUP REQUIRED", "YELLOW")
            print_("=" * 60)
            print_(f"Default config file created at:\n{self.config_file}")
            print_("\nPlease edit the config file with your actual credentials.")
            print_("The file has been opened in your default editor.")
            print_("\nPress Enter after you have saved your changes...")
            print_("=" * 60)
            input()


    def _ensure_config_valid(self) -> None:
        """
        Ensure the configuration is valid.
        """
        if not self._validate_config():
            print_("\nERROR: Configuration is invalid or incomplete!", "RED")
            print_("Please check the following:")
            print_("1. API services are correctly configured")
            print_("2. File paths are valid and exist")
            print_("3. YAML syntax is correct")
            sys.exit(1)

    def _create_config_from_template(self) -> None:
        """Copy credential-example.yaml to user's config directory."""
        template_path = self._get_template_path()

        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")

        # Copy template to user config directory
        shutil.copy(template_path, self.config_file)

    def _open_config_file(self) -> None:
        """Open config file with default system editor."""
        try:
            system = platform.system()

            if system == "Darwin":  # macOS
                subprocess.run(["open", str(self.config_file)])
            elif system == "Windows":
                os.startfile(str(self.config_file))
            elif system == "Linux":
                # Try common Linux editors
                editors = ["xdg-open", "gedit", "kate", "nano", "vim"]
                for editor in editors:
                    if shutil.which(editor):
                        subprocess.run([editor, str(self.config_file)])
                        break
            else:
                print_(f"Please manually open and edit: {self.config_file}", "YELLOW")
        except Exception as e:
            print_(f"Could not auto-open config file: {e}", "RED")
            print_(f"Please manually open and edit: {self.config_file}", "YELLOW")

    def _validate_config(self) -> bool:
        """
        Validate the configuration file.

        Returns:
            True if valid, False otherwise
        """
        try:
            config = self.load_config()

            # Check API services section
            api_services = config.get('api_services', [])

            # Validate API services exist
            if not api_services:
                print_("Error: No API services configured", "RED")
                return False
            
            # Validate each service
            for idx, service in enumerate(api_services, 1):
                # Check required fields are not empty
                api_key = service.get('api_key', '').strip()
                base_url = service.get('base_url', '').strip()
                model = service.get('model', '').strip()
                reasoning_effort = service.get('reasoning_effort', '').strip()
                
                # Validate api_key
                if not api_key:
                    print_(f"Error: Service {idx} - api_key is empty", "RED")
                    return False
                if 'xxxx' in api_key.lower():
                    print_(f"Error: Service {idx} - api_key contains placeholder value", "RED")
                    return False
                
                # Validate base_url
                if not base_url:
                    print_(f"Error: Service {idx} - base_url is empty", "RED")
                    return False
                if not self._is_valid_url(base_url):
                    print_(f"Error: Service {idx} - base_url is not a valid URL: {base_url}", "RED")
                    return False
                
                # Validate model
                if not model:
                    print_(f"Error: Service {idx} - model is empty", "RED")
                    return False
                
                # Validate reasoning_effort
                if not reasoning_effort:
                    print_(f"Error: Service {idx} - reasoning_effort is empty", "RED")
                    return False
                if reasoning_effort not in ['none', 'low', 'medium', 'high']:
                    print_(f"Error: Service {idx} - reasoning_effort must be one of: none, low, medium, high", "RED")
                    return False

            # Check paths section
            paths = config.get('paths', {})
            excel_path = paths.get('excel_file_path', '').strip()
            backup_path = paths.get('backup_folder_path', '').strip()

            # Validate paths are not empty or placeholder
            if not excel_path or '/path/to/' in excel_path:
                print_("Error: excel_file_path is empty or contains placeholder", "RED")
                return False
            
            if not backup_path or '/path/to/' in backup_path:
                print_("Error: backup_folder_path is empty or contains placeholder", "RED")
                return False

            return True

        except Exception as e:
            print_(f"Config validation error: {e}", "RED")
            return False
    
    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """
        Validate if a string is a valid URL.
        
        Args:
            url: URL string to validate
            
        Returns:
            True if valid URL, False otherwise
        """
        try:
            result = urlparse(url)
            # Check if scheme and netloc are present
            return all([result.scheme in ['http', 'https'], result.netloc])
        except Exception:
            return False

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        Returns:
            Dictionary containing configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML parsing fails
        """
        if not self.config_file.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_file}")

        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        return config

    def get_api_services(self) -> list:
        """Get API services list."""
        config = self.load_config()
        return config.get('api_services', [])

    def get_paths_config(self) -> Dict[str, str]:
        """Get paths configuration section."""
        config = self.load_config()
        return config.get('paths', {})


# Initialize global config manager
_config_manager = ConfigManager()
_api_services = _config_manager.get_api_services()
_paths_config = _config_manager.get_paths_config()

# Export configuration variables
API_SERVICES = _api_services

EXCEL_FILE_PATH = _paths_config.get('excel_file_path', '')
BACKUP_FOLDER_PATH = _paths_config.get('backup_folder_path', '')
