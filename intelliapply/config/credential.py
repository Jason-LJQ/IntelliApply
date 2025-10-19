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
import yaml


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
            print(f"Created config directory: {self.config_dir}")

        # Check if config file exists
        if not self.config_file.exists():
            self._create_config_from_template()
            self._open_config_file()
            print("\n" + "=" * 60)
            print("FIRST TIME SETUP REQUIRED")
            print("=" * 60)
            print(f"Default config file created at:\n{self.config_file}")
            print("\nPlease edit the config file with your actual credentials.")
            print("The file has been opened in your default editor.")
            print("\nPress Enter after you have saved your changes...")
            print("=" * 60)
            input()

            # Validate after user edits
            if not self._validate_config():
                print("\nERROR: Configuration is invalid or incomplete!")
                print("Please check the following:")
                print("1. API keys are not placeholder values")
                print("2. File paths are valid and exist")
                print("3. YAML syntax is correct")
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
                print(f"Please manually open and edit: {self.config_file}")
        except Exception as e:
            print(f"Could not auto-open config file: {e}")
            print(f"Please manually open and edit: {self.config_file}")

    def _validate_config(self) -> bool:
        """
        Validate the configuration file.

        Returns:
            True if valid, False otherwise
        """
        try:
            config = self.load_config()

            # Check API section
            api = config.get('api', {})
            api_keys = api.get('api_key_list', [])

            # Validate API keys are not placeholder
            if not api_keys or any('xxxx' in key for key in api_keys):
                return False

            # Check paths section
            paths = config.get('paths', {})
            excel_path = paths.get('excel_file_path', '')
            backup_path = paths.get('backup_folder_path', '')

            # Validate paths are not placeholder
            if '/path/to/' in excel_path or '/path/to/' in backup_path:
                return False

            return True

        except Exception as e:
            print(f"Config validation error: {e}")
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

    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration section."""
        config = self.load_config()
        return config.get('api', {})

    def get_paths_config(self) -> Dict[str, str]:
        """Get paths configuration section."""
        config = self.load_config()
        return config.get('paths', {})


# Initialize global config manager
_config_manager = ConfigManager()
_api_config = _config_manager.get_api_config()
_paths_config = _config_manager.get_paths_config()

# Export configuration variables for backward compatibility
API_KEY_LIST = _api_config.get('api_key_list', [])
BASE_URL = _api_config.get('base_url', 'https://generativelanguage.googleapis.com/v1beta/openai/')
MODEL_LIST = _api_config.get('model_list', ['gemini-2.0-flash-exp'])
REASONING_EFFORT = _api_config.get('reasoning_effort', 'none')

EXCEL_FILE_PATH = _paths_config.get('excel_file_path', '')
BACKUP_FOLDER_PATH = _paths_config.get('backup_folder_path', '')
