from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import graphviz
from python_pubsub_scanner.config_helper import ConfigHelper
from python_pubsub_scanner.scanner import EventFlowScanner


class TestScannerPayload(unittest.TestCase):
    """
    Tests for the EventFlowScanner, using a temporary filesystem to ensure robustness.
    """

    def setUp(self):
        """
        Set up a temporary directory structure and mock external dependencies.
        """
        # 1. Create a real temporary filesystem structure
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)
        self.agents_dir = self.project_root / "agents"
        self.events_dir = self.project_root / "events"
        self.postman_dir = self.project_root / "postman"

        self.agents_dir.mkdir()
        self.events_dir.mkdir()
        self.postman_dir.mkdir()

        # 2. Mock external services and analyzers
        self.requests_post_patcher = patch('python_pubsub_scanner.scanner.requests.post')
        self.analyzer_class_patcher = patch('python_pubsub_scanner.scanner.EventFlowAnalyzer')

        self.mock_post = self.requests_post_patcher.start()
        self.mock_analyzer_class = self.analyzer_class_patcher.start()

        # 3. Configure standard mock behaviors
        mock_analyzer_instance = MagicMock()
        mock_analyzer_instance.get_all_events.return_value = {'event.one', 'event.two'}
        mock_analyzer_instance.subscriptions = {'agent.one': {'event.one'}}
        mock_analyzer_instance.publications = {'agent.two': {'event.two'}}
        mock_analyzer_instance.event_to_subscribers = {'event.one': {'agent.one'}}
        self.mock_analyzer_class.return_value = mock_analyzer_instance

        self.mock_post.return_value.status_code = 201
        self.mock_post.return_value.json.return_value = {'timestamp': '2023-01-01T12:00:00Z'}

    def tearDown(self):
        """
        Clean up the temporary directory and stop all patches.
        """
        self.temp_dir.cleanup()
        patch.stopall()

    def test_payload_structure(self):
        """
        Verify the payload structure using real (temporary) paths.
        """
        scanner = EventFlowScanner(agents_dir=self.agents_dir, events_dir=self.events_dir)
        scanner.scan_once()

        self.assertTrue(self.mock_post.called, "requests.post was not called")
        _, first_call_kwargs = self.mock_post.call_args_list[0]
        payload = first_call_kwargs.get('json')

        self.assertIn('stats', payload)
        self.assertEqual(payload['stats']['events'], 2)
        self.assertEqual(payload['stats']['agents'], 2)

    def test_dot_content_compliance(self):
        """
        Verify the generated dot_content is compliant.
        """
        scanner = EventFlowScanner(agents_dir=self.agents_dir, events_dir=self.events_dir)
        scanner.scan_once()

        self.assertTrue(self.mock_post.called)
        _, kwargs = self.mock_post.call_args_list[0]
        dot_content = kwargs.get('json', {}).get('dot_content')

        try:
            graphviz.Source(dot_content)
        except Exception as e:
            self.fail(f"graphviz failed to parse dot_content. Error: {e}")

    def test_serialization_to_json(self):
        """
        Verify the payload is correctly serialized to JSON.
        """
        scanner = EventFlowScanner(agents_dir=self.agents_dir, events_dir=self.events_dir)
        scanner.scan_once()

        self.assertTrue(self.mock_post.called)
        _, kwargs = self.mock_post.call_args_list[0]
        payload = kwargs.get('json')

        try:
            json.dumps(payload)
        except TypeError as e:
            self.fail(f"Payload is not JSON serializable. Error: {e}")

    def test_from_config_factory_method(self):
        """
        Verify the from_config factory method correctly initializes the scanner.
        """
        mock_config_helper = MagicMock(spec=ConfigHelper)
        mock_config_helper.get_agents_path.return_value = self.agents_dir
        mock_config_helper.get_events_path.return_value = self.events_dir
        mock_config_helper.get_postman_path.return_value = self.postman_dir
        mock_config_helper.get_service_config.return_value = {'port': 1234}

        # The validation in __init__ will now pass because the paths are real.
        scanner = EventFlowScanner.from_config(config=mock_config_helper)

        self.assertEqual(scanner.api_url, "http://localhost:1234")
        self.assertEqual(scanner.agents_dir, self.agents_dir)


if __name__ == '__main__':
    unittest.main()
