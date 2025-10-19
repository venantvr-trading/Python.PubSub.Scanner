# Creating Custom Graph Generators

This guide explains how to create custom graph generators for the Python PubSub Scanner.

## Overview

The scanner uses a pluggable architecture for generating different types of event flow graphs. You can easily create your own custom generators to visualize your
event-driven architecture in new ways.

## Architecture

All graph generators inherit from the `GraphGenerator` abstract base class and implement two key methods:

- `graph_type` property: Returns a unique identifier for the generator
- `generate()` method: Generates DOT content from an analyzer instance

## Creating a Custom Generator

### Step 1: Import the Base Class

```python
from python_pubsub_scanner.graph_generators import GraphGenerator
from python_pubsub_scanner.analyze_event_flow import EventFlowAnalyzer
```

### Step 2: Define Your Generator Class

```python
class MyCustomGenerator(GraphGenerator):
    """
    My custom graph generator that does something special.
    """

    @property
    def graph_type(self) -> str:
        """Return a unique identifier for this generator."""
        return "my-custom-type"

    def generate(self, analyzer: EventFlowAnalyzer, output_path: str = None) -> str:
        """
        Generate DOT content for my custom graph.

        Args:
            analyzer: The EventFlowAnalyzer with parsed event flow data
            output_path: Optional path to write the DOT file

        Returns:
            The generated DOT content as a string
        """
        # Access the analyzer data
        events = analyzer.get_all_events()
        agents = analyzer.get_all_agents()
        namespaces = analyzer.get_all_namespaces()

        # Build your DOT content
        lines = ['digraph MyCustomGraph {']

        # Apply styling options (available from the base class)
        lines.append(f'    graph [fontname="{self.fontname}"];')

        # Add nodes
        for event in sorted(events):
            color = self.colors.get(event.namespace, "#e0e0e0")
            shape = self.shapes.get(event.namespace, "ellipse")
            lines.append(f'    "{event.name}" [fillcolor="{color}", shape={shape}];')

        # Add your custom logic here...

        lines.append('}')
        dot_content = '\\n'.join(lines)

        # Optionally write to file
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(dot_content)

        return dot_content
```

### Step 3: Register Your Generator

```python
from python_pubsub_scanner.graph_generators import register_generator

# Register your custom generator
register_generator('my-custom-type', MyCustomGenerator)
```

### Step 4: Use Your Generator

```python
from python_pubsub_scanner.graph_generators import get_generator
from python_pubsub_scanner.analyze_event_flow import EventFlowAnalyzer

# Create analyzer (assume agents_dir and events_dir are defined)
analyzer = EventFlowAnalyzer(agents_dir, events_dir)
analyzer.analyze()

# Get your custom generator
generator = get_generator(
    'my-custom-type',
    colors={'my_namespace': '#ff0000'},
    shapes={'my_namespace': 'diamond'},
    fontname='Arial'
)

# Generate the graph
dot_content = generator.generate(analyzer)
print(dot_content)
```

## Available Styling Options

The base `GraphGenerator` class provides three styling options that are automatically passed to your generator:

- **colors** (`Dict[str, str]`): Maps namespace names to hex color codes
- **shapes** (`Dict[str, str]`): Maps namespace names to Graphviz node shapes
- **fontname** (`str`): Font name for graph text elements (default: "Arial")

Access these in your generator via:

```python
self.colors
self.shapes
self.fontname
```

## Accessing Analyzer Data

The `EventFlowAnalyzer` instance provides several methods to access the parsed event flow data:

```python
# Get all events (returns Set[NamespacedItem])
events = analyzer.get_all_events()

# Get all agents (returns Set[NamespacedItem])
agents = analyzer.get_all_agents()

# Get all namespaces (returns Set[str])
namespaces = analyzer.get_all_namespaces()

# Get subscription information (Dict[NamespacedItem, List[NamespacedItem]])
subscriptions = analyzer.subscriptions  # agent -> [events]
publications = analyzer.publications  # agent -> [events]

# Get reverse mappings
event_to_subscribers = analyzer.event_to_subscribers  # event -> [agents]
event_to_publishers = analyzer.event_to_publishers  # event -> [agents]
```

### NamespacedItem

Events and agents are represented as `NamespacedItem` objects with two attributes:

```python
class NamespacedItem:
    name: str  # e.g., "UserCreated"
    namespace: str  # e.g., "user_service"
```

## Example: Namespace-Only Graph

Here's a complete example of a generator that creates a graph showing only namespace-level connections:

```python
from collections import defaultdict
from python_pubsub_scanner.graph_generators import GraphGenerator, register_generator


class NamespaceGraphGenerator(GraphGenerator):
    """
    Generates a high-level graph showing connections between namespaces only.
    """

    @property
    def graph_type(self) -> str:
        return "namespace-only"

    def generate(self, analyzer, output_path=None) -> str:
        # Collect namespace-to-namespace connections
        ns_connections = defaultdict(set)

        for agent, publications in analyzer.publications.items():
            agent_ns = agent.namespace
            for event in publications:
                event_ns = event.namespace
                if agent_ns != event_ns:  # Only cross-namespace connections
                    ns_connections[agent_ns].add(event_ns)

        # Build DOT content
        lines = [
            'digraph NamespaceFlow {',
            f'    graph [fontname="{self.fontname}"];',
            '    node [shape=box, style="filled,rounded"];',
            ''
        ]

        # Add namespace nodes
        for namespace in sorted(analyzer.get_all_namespaces()):
            color = self.colors.get(namespace, "#e0e0e0")
            lines.append(f'    "{namespace}" [fillcolor="{color}"];')

        lines.append('')

        # Add edges
        for source_ns in sorted(ns_connections.keys()):
            for target_ns in sorted(ns_connections[source_ns]):
                lines.append(f'    "{source_ns}" -> "{target_ns}";')

        lines.append('}')
        dot_content = '\\n'.join(lines)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(dot_content)

        return dot_content


# Register it
register_generator('namespace-only', NamespaceGraphGenerator)
```

## Integration with Scanner

To use your custom generator with the scanner, you need to modify the scanner's `scan_once()` method to include your new graph type:

```python
# In your scanner initialization or run script
from python_pubsub_scanner.graph_generators import register_generator
from my_generators import NamespaceGraphGenerator

# Register your generator
register_generator('namespace-only', NamespaceGraphGenerator)

# Now you can add 'namespace-only' to the graph_types list in scan_once()
graph_types = ['complete', 'full-tree', 'namespace-only']
```

## Best Practices

1. **Descriptive graph_type**: Use a clear, kebab-case identifier (e.g., "namespace-only", "simplified-flow")

2. **Handle empty data**: Always check if the analyzer has data before generating

3. **Validate output**: Test your generated DOT with Graphviz to ensure it's valid

4. **Document your generator**: Add a clear docstring explaining what the generator does and when to use it

5. **Use styling options**: Respect the colors, shapes, and fontname settings passed to the constructor

6. **Error handling**: Wrap your generation logic in try-except blocks for robustness

## Testing Your Generator

Create unit tests for your custom generator:

```python
import unittest
from unittest.mock import MagicMock
import graphviz

class TestMyCustomGenerator(unittest.TestCase):
    def test_generates_valid_dot(self):
        # Create mock analyzer
        mock_analyzer = MagicMock()
        mock_analyzer.get_all_events.return_value = {...}
        mock_analyzer.get_all_agents.return_value = {...}

        # Create generator
        generator = MyCustomGenerator()

        # Generate DOT
        dot_content = generator.generate(mock_analyzer)

        # Validate with Graphviz
        try:
            graphviz.Source(dot_content)
        except Exception as e:
            self.fail(f"Invalid DOT: {e}")

        # Check content
        self.assertIn('digraph', dot_content)
```

## Contributing

If you create a useful custom generator, consider contributing it back to the project! Open a pull request on GitHub with:

1. Your generator implementation in `src/python_pubsub_scanner/graph_generators/`
2. Tests in `tests/test_graph_generators.py`
3. Documentation updates in this file
4. Example usage in the README

Happy graph generating! 🎨
