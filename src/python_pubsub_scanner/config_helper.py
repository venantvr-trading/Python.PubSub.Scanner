from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


class ConfigHelper:
    """
    A helper to find, load, and validate the master configuration file.

    It starts from a given path and traverses up the directory tree to find the
    project root, identified by the presence of the configuration file.
    It then loads this file, validates key paths, and provides easy access to the configuration.
    """
    CONFIG_FILENAME = "pubsub_devtools.yaml"

    def __init__(self, start_path: str | Path | None = None, config_file_name: str | None = None):
        """
        Initializes the helper and triggers the discovery and validation process.

        Args:
            start_path: The path to start searching from. Defaults to the current working directory.
            config_file_name: The name of the config file to find. Defaults to "pubsub_devtools.yaml".

        Raises:
            FileNotFoundError: If the config file or critical directories are not found.
            ValueError: If the configuration file is malformed.
        """
        if start_path is None:
            start_path = Path.cwd()
        self.start_path = Path(start_path).resolve()

        if config_file_name is None:
            config_file_name = self.CONFIG_FILENAME
        self.config_filename = config_file_name

        # Discovered paths and config
        self.project_root: Path | None = None
        self.config_path: Path | None = None
        self.config: Dict[str, Any] = {}
        self.agents_dir: Path | None = None
        self.events_dir: Path | None = None

        self._find_and_load()
        self._validate_paths()

        print(f"✅ Configuration loaded successfully from: {self.config_path}")

    def _find_and_load(self):
        """Traverse up to find and load the configuration file."""
        # If start_path is a file, start from its parent, otherwise start from the path itself
        current_dir = self.start_path.parent if self.start_path.is_file() else self.start_path

        while current_dir != current_dir.parent:  # Stop at filesystem root
            config_file = current_dir / self.config_filename
            if config_file.is_file() and ".venv" not in str(current_dir):
                self.project_root = current_dir
                self.config_path = config_file
                break
            current_dir = current_dir.parent

        if not self.project_root or not self.config_path:
            raise FileNotFoundError(
                f"Could not find '{self.config_filename}' in any parent directory of {self.start_path}."
            )

        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            if not isinstance(self.config, dict):
                raise ValueError("Config file is not a valid dictionary.")
        except (yaml.YAMLError, ValueError) as e:
            raise ValueError(f"Error parsing '{self.config_path}': {e}")

    def _validate_paths(self):
        """Validate that the directories specified in the config exist."""
        required_dirs = ["agents_dir", "events_dir"]
        for key in required_dirs:
            path_str = self.config.get(key)
            if not path_str:
                raise ValueError(f"'{key}' is not defined in the configuration file.")

            # Path can be relative to the project root
            absolute_path = (self.project_root / path_str).resolve()

            if not absolute_path.is_dir():
                raise FileNotFoundError(
                    f"The directory for '{key}' does not exist: {absolute_path}"
                )

            # Store the validated, absolute path
            setattr(self, key, absolute_path)

    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """
        Returns the specific configuration for a given service.

        Args:
            service_name: The name of the service (e.g., 'event_flow').

        Returns:
            A dictionary of the service's configuration.

        Raises:
            KeyError: if the service is not found in the config.
        """
        if service_name not in self.config:
            raise KeyError(f"Configuration for service '{service_name}' not found.")
        return self.config[service_name]

    def get_agents_path(self) -> Path:
        """
        Returns the validated, absolute path to the agents directory.

        Returns:
            The absolute path to the agents directory.
        """
        return self.agents_dir

    def get_events_path(self) -> Path:
        """
        Returns the validated, absolute path to the events directory.

        Returns:
            The absolute path to the events directory.
        """
        return self.events_dir
