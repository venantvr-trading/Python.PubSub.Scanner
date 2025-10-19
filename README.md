# Python PubSub Scanner

**Autonomous scanner for event-driven architectures** - Scans your codebase for event flow patterns and pushes graph data to a monitoring API.

## Features

- **Code Analysis**: Autonomously scans agent files to detect event subscriptions and publications.
- **Graph Generation**:
    - Generates multiple graph types (e.g., `complete`, `full-tree`).
    - Produces DOT content with CSS classes (`class="namespace-*"`) for easy styling in web frontends.
- **API Integration**:
    - Automatically pushes graph data and statistics to a monitoring API.
    - Generates a Postman collection on successful API push if a `postman` directory is found.
- **Flexible Execution**:
    - Supports one-shot or continuous scanning modes.
    - Configurable via a central `event_flow_config.yaml` file or command-line arguments.

## Installation

```bash
# From source (recommended for development)
git clone https://github.com/venantvr-trading/Python.PubSub.Scanner
cd Python.PubSub.Scanner
pip install -e ".[dev]"
```

## Usage

The recommended way to use the scanner is to combine a central configuration file with programmatic execution.

### 1. Create a Configuration File

At the root of your project, create a `event_flow_config.yaml` file. This allows you to centralize all paths and settings.

```yaml
# event_flow_config.yaml

# === Common Directories ===
agents_dir: "./path/to/your/agents"  # Required
events_dir: "./path/to/your/events"  # Required

# Optional: If this directory exists, a Postman collection will be generated here.
# If this key is omitted, the scanner will look for a "postman" directory
# next to the "agents" directory.
postman_dir: "./postman"

# === Service Configuration ===
port: 5555

# === Graph Styling (Optional) ===
# Customize the appearance of your event flow graphs
namespaces_colors:
  bot_lifecycle: "#81c784"
  market_data: "#64b5f6"

namespaces_shapes:
  bot_lifecycle: "box"
  market_data: "ellipse"

graph_fontname: "Arial"
```

### 2. Run Programmatically (Recommended)

Create a Python script to run the scanner. This approach is robust, as it ensures all paths are validated and decouples the scanner's initialization from hardcoded paths.

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
        helper = ConfigHelper(config_file_name="event_flow_config.yaml")

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

### 3. Command-Line Usage

For quick scans or simple use cases, you can run the scanner directly from the command line.

**Example:**

```bash
pubsub-scanner \
    --agents-dir /path/to/your/agents \
    --events-dir /path/to/your/events \
    --api-url http://localhost:5555 \
    --one-shot
```

**Options:**

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
