from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import graphviz

from python_pubsub_scanner.analyze_event_flow import EventFlowAnalyzer, NamespacedItem
from python_pubsub_scanner.graph_generators import (
    get_generator,
    register_generator,
    AVAILABLE_GENERATORS,
    GraphGenerator,
    CompleteGraphGenerator,
    FullTreeGraphGenerator
)


class TestGraphGenerators(unittest.TestCase):
    """
    Tests for the graph_generators module and its generator classes.
    """

    def setUp(self):
        """Set up mock analyzer with test data."""
        # Create test NamespacedItems
        self.event_one = NamespacedItem(name="EventOne", namespace="test_namespace")
        self.event_two = NamespacedItem(name="EventTwo", namespace="test_namespace")
        self.agent_one = NamespacedItem(name="AgentOne", namespace="test_agents")
        self.agent_two = NamespacedItem(name="AgentTwo", namespace="test_agents")

        # Create a mock analyzer
        self.mock_analyzer = MagicMock(spec=EventFlowAnalyzer)
        self.mock_analyzer.get_all_events.return_value = {self.event_one, self.event_two}
        self.mock_analyzer.get_all_agents.return_value = {self.agent_one, self.agent_two}
        self.mock_analyzer.get_all_namespaces.return_value = {'test_namespace', 'test_agents'}
        self.mock_analyzer.subscriptions = {self.agent_one: [self.event_one]}
        self.mock_analyzer.publications = {self.agent_two: [self.event_two]}
        self.mock_analyzer.event_to_subscribers = {self.event_one: [self.agent_one]}

    def test_available_generators(self):
        """Verify that the list of available generators includes expected types."""
        self.assertIn('complete', AVAILABLE_GENERATORS)
        self.assertIn('full-tree', AVAILABLE_GENERATORS)

    def test_get_generator_complete(self):
        """Verify get_generator returns CompleteGraphGenerator for 'complete' type."""
        generator = get_generator('complete')
        self.assertIsInstance(generator, CompleteGraphGenerator)
        self.assertEqual(generator.graph_type, 'complete')

    def test_get_generator_full_tree(self):
        """Verify get_generator returns FullTreeGraphGenerator for 'full-tree' type."""
        generator = get_generator('full-tree')
        self.assertIsInstance(generator, FullTreeGraphGenerator)
        self.assertEqual(generator.graph_type, 'full-tree')

    def test_get_generator_with_styling(self):
        """Verify get_generator passes styling options to the generator."""
        colors = {"test_namespace": "#ff0000"}
        shapes = {"test_namespace": "diamond"}
        fontname = "Courier"

        generator = get_generator('complete', colors=colors, shapes=shapes, fontname=fontname)

        self.assertEqual(generator.colors, colors)
        self.assertEqual(generator.shapes, shapes)
        self.assertEqual(generator.fontname, fontname)

    def test_get_generator_unknown_type(self):
        """Verify get_generator raises ValueError for unknown graph type."""
        with self.assertRaises(ValueError) as ctx:
            get_generator('unknown_type')

        self.assertIn('unknown_type', str(ctx.exception))
        self.assertIn('complete', str(ctx.exception))
        self.assertIn('full-tree', str(ctx.exception))

    def test_complete_generator_produces_valid_dot(self):
        """Verify CompleteGraphGenerator produces valid DOT content."""
        generator = CompleteGraphGenerator()
        dot_content = generator.generate(self.mock_analyzer)

        # Verify it's valid DOT by trying to parse it with graphviz
        try:
            graphviz.Source(dot_content)
        except Exception as e:
            self.fail(f"Generated DOT content is invalid: {e}")

        # Verify content includes expected elements
        self.assertIn('digraph EventFlow', dot_content)
        self.assertIn('EventOne', dot_content)
        self.assertIn('EventTwo', dot_content)
        self.assertIn('AgentOne', dot_content)
        self.assertIn('AgentTwo', dot_content)

    def test_complete_generator_with_colors(self):
        """Verify CompleteGraphGenerator applies custom colors."""
        colors = {"test_namespace": "#123456"}
        generator = CompleteGraphGenerator(colors=colors)
        dot_content = generator.generate(self.mock_analyzer)

        self.assertIn('#123456', dot_content)

    def test_complete_generator_with_shapes(self):
        """Verify CompleteGraphGenerator applies custom shapes."""
        shapes = {"test_namespace": "diamond"}
        generator = CompleteGraphGenerator(shapes=shapes)
        dot_content = generator.generate(self.mock_analyzer)

        self.assertIn('shape=diamond', dot_content)

    def test_complete_generator_with_fontname(self):
        """Verify CompleteGraphGenerator applies custom fontname."""
        generator = CompleteGraphGenerator(fontname="Courier")
        dot_content = generator.generate(self.mock_analyzer)

        self.assertIn('fontname="Courier"', dot_content)

    def test_complete_generator_writes_to_file(self):
        """Verify CompleteGraphGenerator can write output to a file."""
        generator = CompleteGraphGenerator()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            output_path = f.name

        try:
            dot_content = generator.generate(self.mock_analyzer, output_path=output_path)

            # Verify the file was created and contains the same content
            with open(output_path, 'r') as f:
                file_content = f.read()

            self.assertEqual(dot_content, file_content)
            self.assertIn('digraph EventFlow', file_content)
        finally:
            Path(output_path).unlink()

    def test_full_tree_generator_produces_valid_dot(self):
        """Verify FullTreeGraphGenerator produces valid DOT content."""
        generator = FullTreeGraphGenerator()
        dot_content = generator.generate(self.mock_analyzer)

        # Verify it's valid DOT by trying to parse it with graphviz
        try:
            graphviz.Source(dot_content)
        except Exception as e:
            self.fail(f"Generated DOT content is invalid: {e}")

        # Verify content includes expected elements
        self.assertIn('digraph EventFlow', dot_content)

    def test_register_custom_generator(self):
        """Verify that custom generators can be registered."""
        class CustomGenerator(GraphGenerator):
            @property
            def graph_type(self) -> str:
                return "custom"

            def generate(self, analyzer, output_path=None) -> str:
                return "digraph Custom { }"

        # Register the custom generator
        register_generator('custom', CustomGenerator)

        # Verify we can get it (which proves it was registered)
        generator = get_generator('custom')
        self.assertIsInstance(generator, CustomGenerator)

        # Verify it generates content
        dot_content = generator.generate(self.mock_analyzer)
        self.assertEqual(dot_content, "digraph Custom { }")

    def test_namespace_classes_in_output(self):
        """Verify that namespace classes are included in the DOT output."""
        generator = CompleteGraphGenerator()
        dot_content = generator.generate(self.mock_analyzer)

        # Verify namespace classes are present
        self.assertIn('class="namespace-test_namespace"', dot_content)
        self.assertIn('class="namespace-test_agents"', dot_content)


if __name__ == '__main__':
    unittest.main()
