# Python PubSub Scanner

**Autonomous scanner for event-driven architectures** - Scans your codebase for event flow patterns and pushes graph data to a monitoring API.

## Features

- **Code Analysis**: Autonomously scans agent files to detect event subscriptions and publications.
- **Graph Generation**:
    - Generates multiple graph types (complete, full-tree).
    - Pluggable architecture: easily create custom graph generators.
    - Produces DOT content with CSS classes (`namespace-*`) for easy styling in web frontends.
    - Supports custom colors, shapes, and fonts per namespace.
- **API Integration**:
    - Automatically pushes graph data and statistics to a monitoring API.
    - Generates a Postman collection on successful API push if a `postman` directory is found.
- **Flexible Execution**:
    - Supports one-shot or continuous scanning modes.
    - Configurable via a central `devtools_config.yaml` file or command-line arguments.

## Installation

```bash
# From source (recommended for development)
git clone https://github.com/venantvr-trading/Python.PubSub.Scanner
cd Python.PubSub.Scanner
pip install -e ".[dev]"
```

## Usage

### 1. Create a Configuration File

The recommended way to use the scanner is with a central configuration file. At the root of your project, create a `devtools_config.yaml` file.

```yaml
# devtools_config.yaml

# === Common Directories ===
agents_dir: "./path/to/your/agents"  # Required
events_dir: "./path/to/your/events"  # Required

# Optional: If this directory exists, a Postman collection will be generated here.
# If this key is omitted, the scanner will look for a "postman" directory
# next to the "agents" directory.
postman_dir: "./postman"

# === Service Configurations ===
event_flow:
  port: 5555

# === Graph Styling (Optional) ===
# Customize the appearance of your event flow graphs

# Namespace colors: Map namespace names to hex color codes
namespaces_colors:
  bot_lifecycle: "#81c784"  # green
  market_data: "#64b5f6"    # blue
  indicator: "#9575cd"      # purple
  internal: "#ba68c8"       # purple light
  capital: "#ffd54f"        # yellow
  pool: "#ffb74d"           # orange
  position: "#ff8a65"       # deep orange
  exchange: "#4dd0e1"       # cyan
  command: "#a1887f"        # brown
  database: "#90a4ae"       # blue grey
  exit_strategy: "#aed581"  # light green
  query: "#81d4fa"          # light blue
  unknown: "#e0e0e0"        # grey

# Namespace shapes: Map namespace names to Graphviz node shapes
# Common shapes: box, ellipse, circle, diamond, triangle, hexagon, octagon
namespaces_shapes:
  bot_lifecycle: "box"
  market_data: "ellipse"
  indicator: "diamond"

# Font name for graph text elements
graph_fontname: "Arial"
```

### 2. Run Programmatically (Recommended)

Create a Python script to run the scanner. This approach is robust as it ensures all paths are validated and decouples the scanner's initialization from hardcoded paths.

```python
# run_scanner.py
from python_pubsub_scanner.config_helper import ConfigHelper
from python_pubsub_scanner.scanner import EventFlowScanner


def main():
    """
    Initializes and runs the scanner using the central configuration.
    """
    try:
        # 1. Initialize the helper. It finds and validates the config automatically.
        helper = ConfigHelper(config_file_name="devtools_config.yaml")

        # 2. Use the factory method to create a fully configured scanner.
        scanner = EventFlowScanner.from_config(config=helper)

        # 3. Execute a one-shot scan.
        results = scanner.scan_once()
        print(f"\n✅ Scan complete. Results: {results}")

    except (FileNotFoundError, ValueError, KeyError) as e:
        print(f"❌ Configuration Error: {e}")


if __name__ == "__main__":
    main()
```

### 3. Alternative: Run from the Command Line

You can still run the scanner directly from the command line. Note that `--events-dir` is now required.

```bash
pubsub-scanner \
    --agents-dir /path/to/your/agents \
    --events-dir /path/to/your/events \
    --api-url http://localhost:5555 \
    --one-shot
```

## Command-Line Options

```
usage: pubsub-scanner [-h] --agents-dir AGENTS_DIR --events-dir EVENTS_DIR
                      [--api-url API_URL] [--interval INTERVAL] [--one-shot]
                      [--version]

Event Flow Scanner - Scan codebase and push graphs to API

options:
  -h, --help            show this help message and exit
  --agents-dir AGENTS_DIR
                        Path to agents directory (required)
  --events-dir EVENTS_DIR
                        Path to events directory (required)
  --api-url API_URL     Base URL of event_flow API (default: http://localhost:5555)
  --interval INTERVAL   Scan interval in seconds (omit for one-shot mode)
  --one-shot            Run once and exit (overrides --interval)
  --version             show program's version number and exit
```

## Custom Graph Generators

The scanner uses a pluggable architecture for graph generation. You can easily create custom generators to visualize your event flow in new ways.

### Creating a Custom Generator

```python
from python_pubsub_scanner.graph_generators import GraphGenerator, register_generator


class MyCustomGenerator(GraphGenerator):

    @property
    def graph_type(self) -> str:
        return "my-custom-type"

    def generate(self, analyzer, output_path=None) -> str:
        # Access analyzer data
        events = analyzer.get_all_events()
        agents = analyzer.get_all_agents()

        # Build your DOT content
        lines = ['digraph Custom {']

        # Use styling options
        for event in events:
            color = self.colors.get(event.namespace, "#e0e0e0")
            lines.append(f'    "{event.name}" [fillcolor="{color}"];')

        lines.append('}')
        return '\n'.join(lines)


# Register your generator
register_generator('my-custom-type', MyCustomGenerator)

# Use it
from python_pubsub_scanner.graph_generators import get_generator

generator = get_generator('my-custom-type', colors={...})
dot_content = generator.generate(analyzer)
```

For a complete guide on creating custom generators, see [docs/CUSTOM_GENERATORS.md](docs/CUSTOM_GENERATORS.md).

## Development

Use the provided Makefile for common development tasks.

```bash
# Install dependencies
make install-dev

# Run all checks (format, lint, test)
make check

# Run tests only
make test
```

## License

MIT License - See LICENSE file for details.
