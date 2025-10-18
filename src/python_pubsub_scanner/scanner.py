"""
Event Flow Scanner - Autonomous service to scan codebase and push graphs to API.

Scans agent code periodically, generates graph data, and POSTs to the event_flow API.
Can run in one-shot mode or continuous mode with a configurable interval.

Library Usage:
    To use this scanner as a library in your own Python project, you can import
    and run it as follows.

    Example:
        from pathlib import Path
        from python_pubsub_scanner.scanner import EventFlowScanner

        def run_scan():
            # Example of running the event flow scanner.
            agents_path = Path("/path/to/your/project/agents")
            api_endpoint = "http://localhost:5555"

            print(f"Starting scanner for directory: {agents_path}")

            try:
                # Initialize the scanner for a one-shot scan.
                scanner = EventFlowScanner(
                    agents_dir=agents_path,
                    api_url=api_endpoint
                )

                # Execute the scan.
                results = scanner.scan_once()

                print("\nScan finished.")
                print("Results:")
                for graph_type, success in results.items():
                    status = "✅ Success" if success else "❌ Failed"
                    print(f"  - Graph '{graph_type}': {status}")

            except ValueError as e:
                print(f"Initialization Error: {e}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

        if __name__ == "__main__":
            run_scan()
"""
from __future__ import annotations

import tempfile
import time
from pathlib import Path
from typing import Optional, Dict, Set, Any

import requests

# Import from local modules (zero external dependencies)
from .analyze_event_flow import EventFlowAnalyzer
from .generate_hierarchical_tree import generate_hierarchical_tree


class EventFlowScanner:
    """
    Scanner service that analyzes event flow and pushes to API

    Attributes:
        agents_dir: Directory containing agent code
        events_dir: Directory containing event definitions
        api_url: Base URL of the event_flow API
        interval: Scan interval in seconds (None for one-shot)
    """

    def __init__(
            self,
            agents_dir: Path,
            events_dir: Optional[Path] = None,
            api_url: str = "http://localhost:5555",
            interval: Optional[int] = None,
    ):
        """
        Initialize scanner

        Args:
            agents_dir: Path to agents directory
            events_dir: Path to events directory (optional, for namespace info)
            api_url: Base URL of event_flow API
            interval: Scan interval in seconds (None for one-shot mode)
        """
        self.agents_dir = agents_dir
        self.events_dir = events_dir
        self.api_url = api_url.rstrip('/')
        self.interval = interval

        # Validate paths
        if not self.agents_dir.exists():
            raise ValueError(f"Agents directory not found: {self.agents_dir}")

    def scan_once(self) -> Dict[str, bool]:
        """
        Perform a single scan and push to API

        Returns:
            Dictionary mapping graph_type to success status
        """
        print(f"[SCAN] Starting scan at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[SCAN] Agents directory: {self.agents_dir}")

        # Analyze event flow using python_pubsub_devtools
        analyzer = EventFlowAnalyzer(self.agents_dir)
        analyzer.analyze()

        events = analyzer.get_all_events()
        agents = set(analyzer.subscriptions.keys()) | set(analyzer.publications.keys())

        print(f"[SCAN] Found {len(events)} events, {len(agents)} agents")

        # Collect namespaces if events_dir available
        namespaces = self._get_namespaces() if self.events_dir else None

        # Generate and push each graph type
        graph_types = ['complete', 'full-tree']
        results = {}

        for graph_type in graph_types:
            try:
                print(f"[SCAN] Generating {graph_type} graph...")
                dot_content = self._generate_dot(analyzer, graph_type)

                if dot_content:
                    # Calculate connections (subscriptions + publications)
                    total_connections = 0
                    for event, subscribers in analyzer.event_to_subscribers.items():
                        total_connections += len(subscribers)
                    for agent, publications in analyzer.publications.items():
                        total_connections += len(publications)

                    # Prepare payload
                    payload: Dict[str, Any] = {
                        'graph_type': graph_type,
                        'dot_content': dot_content,
                        'stats': {
                            'events': len(events),
                            'agents': len(agents),
                            'connections': total_connections,
                        }
                    }

                    if namespaces:
                        payload['namespaces'] = list(namespaces)

                    # POST to API
                    success = self._push_to_api(payload)
                    results[graph_type] = success
                else:
                    print(f"[SCAN] Failed to generate {graph_type}")
                    results[graph_type] = False

            except Exception as e:
                print(f"[SCAN] Error processing {graph_type}: {e}")
                results[graph_type] = False

        return results

    def run_continuous(self) -> None:
        """
        Run scanner in continuous mode with configured interval

        Raises:
            ValueError: If interval is None
        """
        if self.interval is None:
            raise ValueError("Cannot run continuous mode without interval")

        print(f"[SCAN] Starting continuous scanner (interval: {self.interval}s)")
        print(f"[SCAN] API URL: {self.api_url}")
        print(f"[SCAN] Press Ctrl+C to stop")
        print()

        try:
            while True:
                results = self.scan_once()

                # Print summary
                success_count = sum(1 for s in results.values() if s)
                total_count = len(results)
                print(f"[SCAN] Completed: {success_count}/{total_count} graphs pushed successfully")
                print()

                # Wait for next cycle
                print(f"[SCAN] Sleeping for {self.interval} seconds...")
                time.sleep(self.interval)

        except KeyboardInterrupt:
            print("\n[SCAN] Stopped by user")

    def _generate_dot(self, analyzer: EventFlowAnalyzer, graph_type: str) -> Optional[str]:
        """
        Generate DOT content for specified graph type

        Args:
            analyzer: EventFlowAnalyzer instance with analysis results
            graph_type: Type of graph (complete, full-tree)

        Returns:
            DOT content as string, or None if generation fails
        """
        # Use a temporary file that is automatically cleaned up
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.dot', delete=True, encoding='utf-8') as temp_f:
            dot_file_path = temp_f.name
            try:
                if graph_type == 'complete':
                    # Generate complete graph (simplified version without namespace colors)
                    dot_content = self._generate_complete_dot(analyzer)
                    temp_f.write(dot_content)
                elif graph_type == 'full-tree':
                    generate_hierarchical_tree(analyzer, dot_file_path, output_format='dot')
                else:
                    print(f"[SCAN] Unknown graph type: {graph_type}")
                    return None

                temp_f.seek(0)  # Rewind to read the content
                return temp_f.read()
            except Exception as e:
                print(f"[SCAN] Error generating DOT for {graph_type}: {e}")
                return None

    # noinspection PyMethodMayBeStatic
    def _generate_complete_dot(self, analyzer: EventFlowAnalyzer) -> str:
        """
        Generate DOT content for complete graph

        Args:
            analyzer: EventFlowAnalyzer with analysis results

        Returns:
            DOT content as string
        """
        lines = ['digraph EventFlow {',
                 '    rankdir=TB;',
                 '    node [shape=box, style="filled,rounded", fontname="Arial", fontsize=10];',
                 '    edge [arrowsize=0.8];',
                 '']

        events = analyzer.get_all_events()
        agents = set(analyzer.subscriptions.keys()) | set(analyzer.publications.keys())

        # Add event nodes
        for event in sorted(events):
            lines.append(f'    "{event}" [fillcolor="#e0e0e0", shape=ellipse];')

        # Add agent nodes
        for agent in sorted(agents):
            lines.append(f'    "{agent}" [fillcolor="#ffcc80"];')

        lines.append('')

        # Add edges
        for event, subscribers in sorted(analyzer.event_to_subscribers.items()):
            for subscriber in subscribers:
                lines.append(f'    "{event}" -> "{subscriber}";')

        for agent, publications in sorted(analyzer.publications.items()):
            for event in publications:
                lines.append(f'    "{agent}" -> "{event}";')

        lines.append('}')
        return '\n'.join(lines)

    def _get_namespaces(self) -> Set[str]:
        """
        Get all event namespaces by scanning events directory

        Returns:
            Set of namespace names
        """
        if not self.events_dir or not self.events_dir.exists():
            return set()

        namespaces = set()
        for namespace_dir in self.events_dir.iterdir():
            if namespace_dir.is_dir() and not namespace_dir.name.startswith('__'):
                namespaces.add(namespace_dir.name)

        return namespaces

    def _push_to_api(self, payload: Dict) -> bool:
        """
        POST graph data to API

        Args:
            payload: Dictionary with graph data

        Returns:
            True if successful, False otherwise
        """
        endpoint = f"{self.api_url}/api/graph"

        try:
            response = requests.post(
                endpoint,
                json=payload,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 201:
                result = response.json()
                print(f"[SCAN] ✅ Pushed {payload['graph_type']} successfully")
                print(f"[SCAN]    Timestamp: {result.get('timestamp')}")
                return True
            else:
                print(f"[SCAN] ❌ Failed to push {payload['graph_type']}: {response.status_code}")
                print(f"[SCAN]    Response: {response.text}")
                return False

        except requests.exceptions.ConnectionError:
            print(f"[SCAN] ❌ Connection error - is API running at {self.api_url}?")
            return False
        except requests.exceptions.Timeout:
            print(f"[SCAN] ❌ Request timeout")
            return False
        except Exception as e:
            print(f"[SCAN] ❌ Unexpected error pushing to API: {e}")
            return False
