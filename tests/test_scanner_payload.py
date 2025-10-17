from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import graphviz

from python_pubsub_scanner.scanner import EventFlowScanner


class TestScannerPayload(unittest.TestCase):
    """
    Tests to validate the structure, compliance, and serialization of the payload sent to the API.
    """

    def setUp(self):
        """
        Set up common mocks for all tests in this class.
        """
        self.path_exists_patcher = patch('pathlib.Path.exists', return_value=True)
        self.requests_post_patcher = patch('python_pubsub_scanner.scanner.requests.post')
        self.analyzer_class_patcher = patch('python_pubsub_scanner.scanner.EventFlowAnalyzer')
        self.iterdir_patcher = patch('pathlib.Path.iterdir')

        self.mock_path_exists = self.path_exists_patcher.start()
        self.mock_post = self.requests_post_patcher.start()
        self.mock_analyzer_class = self.analyzer_class_patcher.start()
        self.mock_iterdir = self.iterdir_patcher.start()

        # Configure mocks
        mock_analyzer_instance = MagicMock()
        mock_analyzer_instance.get_all_events.return_value = {'event.one', 'event.two'}
        mock_analyzer_instance.subscriptions = {'agent.one': {'event.one'}}
        mock_analyzer_instance.publications = {'agent.two': {'event.two'}}
        mock_analyzer_instance.event_to_subscribers = {'event.one': {'agent.one'}}
        self.mock_analyzer_class.return_value = mock_analyzer_instance

        self.mock_post.return_value.status_code = 201
        self.mock_post.return_value.json.return_value = {'timestamp': '2023-01-01T12:00:00Z'}

        # Mock iterdir to simulate namespace directories
        mock_ns_dir1 = MagicMock(spec=Path)
        mock_ns_dir1.is_dir.return_value = True
        mock_ns_dir1.name = 'ns1'
        mock_ns_dir2 = MagicMock(spec=Path)
        mock_ns_dir2.is_dir.return_value = True
        mock_ns_dir2.name = 'ns2'
        self.mock_iterdir.return_value = [mock_ns_dir1, mock_ns_dir2]

    def tearDown(self):
        """
        Clean up mocks after each test.
        """
        self.path_exists_patcher.stop()
        self.requests_post_patcher.stop()
        self.analyzer_class_patcher.stop()
        self.iterdir_patcher.stop()

    def test_payload_structure(self):
        """
        Verify that the payload sent to the API has the correct structure and types.
        """
        scanner = EventFlowScanner(agents_dir=Path('/dummy/path'))
        scanner.scan_once()

        self.assertTrue(self.mock_post.called, "requests.post was not called")
        self.assertEqual(self.mock_post.call_count, 2, "requests.post was not called twice")

        _, first_call_kwargs = self.mock_post.call_args_list[0]
        payload = first_call_kwargs.get('json')

        self.assertIsNotNone(payload, "Payload should not be None")
        self.assertIn('graph_type', payload)
        self.assertIn('dot_content', payload)
        self.assertIn('stats', payload)
        self.assertIsInstance(payload['graph_type'], str)
        self.assertIsInstance(payload['dot_content'], str)
        self.assertIsInstance(payload['stats'], dict)

        stats = payload['stats']
        self.assertIn('events', stats)
        self.assertIn('agents', stats)
        self.assertIn('connections', stats)
        self.assertIsInstance(stats['events'], int)
        self.assertIsInstance(stats['agents'], int)
        self.assertIsInstance(stats['connections'], int)

        self.assertEqual(stats['events'], 2)
        self.assertEqual(stats['agents'], 2)
        self.assertEqual(stats['connections'], 2)

    def test_dot_content_compliance(self):
        """
        Verify that the generated dot_content is compliant with the DOT language.
        """
        scanner = EventFlowScanner(agents_dir=Path('/dummy/path'))
        scanner.scan_once()

        self.assertTrue(self.mock_post.called, "requests.post was not called")

        for call in self.mock_post.call_args_list:
            _, kwargs = call
            payload = kwargs.get('json')
            dot_content = payload.get('dot_content')
            graph_type = payload.get('graph_type')

            self.assertIsNotNone(dot_content, f"dot_content for {graph_type} should not be None")
            self.assertTrue(len(dot_content) > 0, f"dot_content for {graph_type} should not be empty")

            try:
                graphviz.Source(dot_content)
            except Exception as e:
                self.fail(f"graphviz failed to parse dot_content for '{graph_type}'. Error: {e}")

    def test_serialization_to_json(self):
        """
        Verify that the payload is correctly serialized to JSON, including converting sets to lists.
        """
        scanner = EventFlowScanner(agents_dir=Path('/dummy/agents'), events_dir=Path('/dummy/events'))
        scanner.scan_once()

        self.assertTrue(self.mock_post.called, "requests.post was not called")

        _, kwargs = self.mock_post.call_args_list[0]
        payload = kwargs.get('json')

        self.assertIn('namespaces', payload, "Namespaces key should be in payload")
        self.assertIsInstance(payload['namespaces'], list, "Namespaces should be a list for JSON serialization")
        self.assertCountEqual(payload['namespaces'], ['ns1', 'ns2'])

        try:
            json_string = json.dumps(payload)
        except TypeError as e:
            self.fail(f"Payload is not JSON serializable. Error: {e}")

        try:
            json.loads(json_string)
        except json.JSONDecodeError as e:
            self.fail(f"Failed to decode the generated JSON string: {e}")


if __name__ == '__main__':
    unittest.main()
