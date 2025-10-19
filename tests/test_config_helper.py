from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict

import yaml

from python_pubsub_scanner.config_helper import ConfigHelper


class TestConfigHelper(unittest.TestCase):
    """
    Tests for the ConfigHelper class to ensure it correctly finds, loads,
    and validates configuration files and paths.
    """

    def setUp(self):
        """Set up a temporary directory structure for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)

        # Create a realistic but fake project structure
        self.agents_dir = self.project_root / "src" / "agents"
        self.events_dir = self.project_root / "src" / "events"
        self.postman_dir = self.project_root / "src" / "postman"
        self.start_dir = self.project_root / "scripts"

        self.agents_dir.mkdir(parents=True)
        self.events_dir.mkdir(parents=True)
        self.start_dir.mkdir()

        # Default config data (type annotation to allow any value types)
        self.config_data: Dict[str, Any] = {
            "agents_dir": "./src/agents",
            "events_dir": "./src/events",
            "port": 9999
        }

    def tearDown(self):
        """Clean up the temporary directory."""
        self.temp_dir.cleanup()

    def _write_config(self, data):
        with open(self.project_root / "event_flow_config.yaml", "w") as f:
            yaml.dump(data, f)

    def test_successful_init_from_script_path(self):
        """Verify successful initialization when starting from a subdirectory."""
        self._write_config(self.config_data)
        helper = ConfigHelper(start_path=self.start_dir, config_file_name="event_flow_config.yaml")

        self.assertEqual(helper.project_root, self.project_root)
        self.assertEqual(helper.get_agents_path(), self.agents_dir)
        self.assertEqual(helper.get_events_path(), self.events_dir)
        self.assertIsNone(helper.get_postman_path(), "Postman path should be None as it does not exist yet")

    def test_raises_error_if_required_dir_missing(self):
        """Verify it raises FileNotFoundError if a configured directory does not exist."""
        self.config_data["agents_dir"] = "./src/non_existent_agents"
        self._write_config(self.config_data)

        with self.assertRaises(FileNotFoundError) as ctx:
            ConfigHelper(start_path=self.start_dir, config_file_name="event_flow_config.yaml")
        self.assertIn("non_existent_agents", str(ctx.exception))

    def test_postman_dir_explicit_and_exists(self):
        """Verify Postman dir is found when explicitly configured and it exists."""
        self.postman_dir.mkdir()  # Ensure the directory exists
        self.config_data["postman_dir"] = "./src/postman"
        self._write_config(self.config_data)

        helper = ConfigHelper(start_path=self.start_dir, config_file_name="event_flow_config.yaml")
        self.assertEqual(helper.get_postman_path(), self.postman_dir)

    def test_postman_dir_guessed_and_exists(self):
        """Verify Postman dir is found by guessing when it exists next to agents dir."""
        # In this test, postman_dir is NOT in the config file.
        # We create the directory, so the helper should find it by guessing.
        (self.agents_dir.parent / "postman").mkdir()
        self._write_config(self.config_data)

        helper = ConfigHelper(start_path=self.start_dir, config_file_name="event_flow_config.yaml")
        expected_path = (self.agents_dir.parent / "postman").resolve()
        self.assertEqual(helper.get_postman_path(), expected_path)

    def test_postman_dir_is_none_if_not_exists(self):
        """Verify Postman dir is None if it's not in config and doesn't exist at the guessed location."""
        # Directory is not created and not in config
        self._write_config(self.config_data)
        helper = ConfigHelper(start_path=self.start_dir, config_file_name="event_flow_config.yaml")
        self.assertIsNone(helper.get_postman_path())

    def test_get_namespaces_colors(self):
        """Verify it correctly returns namespace color mappings from config."""
        self.config_data["namespaces_colors"] = {
            "bot_lifecycle": "#81c784",
            "market_data": "#64b5f6",
            "indicator": "#9575cd"
        }
        self._write_config(self.config_data)
        helper = ConfigHelper(start_path=self.start_dir, config_file_name="event_flow_config.yaml")

        colors = helper.get_namespaces_colors()
        self.assertEqual(colors["bot_lifecycle"], "#81c784")
        self.assertEqual(colors["market_data"], "#64b5f6")
        self.assertEqual(colors["indicator"], "#9575cd")
        self.assertEqual(len(colors), 3)

    def test_get_namespaces_colors_empty_when_not_configured(self):
        """Verify it returns an empty dict when namespaces_colors is not in config."""
        self._write_config(self.config_data)
        helper = ConfigHelper(start_path=self.start_dir, config_file_name="event_flow_config.yaml")

        colors = helper.get_namespaces_colors()
        self.assertEqual(colors, {})

    def test_get_namespaces_shapes(self):
        """Verify it correctly returns namespace shape mappings from config."""
        self.config_data["namespaces_shapes"] = {
            "bot_lifecycle": "box",
            "market_data": "ellipse",
            "indicator": "diamond"
        }
        self._write_config(self.config_data)
        helper = ConfigHelper(start_path=self.start_dir, config_file_name="event_flow_config.yaml")

        shapes = helper.get_namespaces_shapes()
        self.assertEqual(shapes["bot_lifecycle"], "box")
        self.assertEqual(shapes["market_data"], "ellipse")
        self.assertEqual(shapes["indicator"], "diamond")
        self.assertEqual(len(shapes), 3)

    def test_get_namespaces_shapes_empty_when_not_configured(self):
        """Verify it returns an empty dict when namespaces_shapes is not in config."""
        self._write_config(self.config_data)
        helper = ConfigHelper(start_path=self.start_dir, config_file_name="event_flow_config.yaml")

        shapes = helper.get_namespaces_shapes()
        self.assertEqual(shapes, {})

    def test_get_graph_fontname(self):
        """Verify it correctly returns the graph fontname from config."""
        self.config_data["graph_fontname"] = "Verdana"
        self._write_config(self.config_data)
        helper = ConfigHelper(start_path=self.start_dir, config_file_name="event_flow_config.yaml")

        fontname = helper.get_graph_fontname()
        self.assertEqual(fontname, "Verdana")

    def test_get_graph_fontname_none_when_not_configured(self):
        """Verify it returns None when graph_fontname is not in config."""
        self._write_config(self.config_data)
        helper = ConfigHelper(start_path=self.start_dir, config_file_name="event_flow_config.yaml")

        fontname = helper.get_graph_fontname()
        self.assertIsNone(fontname)


if __name__ == '__main__':
    unittest.main()
