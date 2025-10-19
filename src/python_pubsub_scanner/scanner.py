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
            events_path = Path("/path/to/your/project/events")
            api_endpoint = "http://localhost:5555"

            print(f"Starting scanner for directory: {agents_path}")

            try:
                # Initialize the scanner for a one-shot scan.
                scanner = EventFlowScanner(
                    agents_dir=agents_path,
                    events_dir=events_path,
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

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse

import requests

from .analyze_event_flow import EventFlowAnalyzer
from .anomaly_detector import AnomalyDetector
from .config_helper import ConfigHelper
from .graph_generators import get_generator


class EventFlowScanner:
    """
    Scanner service that analyzes event flow and pushes to API
    """

    def __init__(
            self,
            agents_dir: Path,
            events_dir: Path,
            postman_dir: Optional[Path] = None,
            api_url: str = "http://localhost:5555",
            interval: Optional[int] = None,
            colors: Optional[Dict[str, str]] = None,
            shapes: Optional[Dict[str, str]] = None,
            fontname: Optional[str] = None
    ):
        """
        Initialize scanner

        Args:
            agents_dir: Path to agents directory.
            events_dir: Path to events directory for namespace info.
            postman_dir: Path to directory for Postman collections (optional).
            api_url: Base URL of event_flow API.
            interval: Scan interval in seconds (None for one-shot mode).
            colors: A dictionary mapping a namespace to a fill color (e.g., {"user_service": "#ff0000"}).
            shapes: A dictionary mapping a namespace to a node shape.
                   Common Graphviz shapes include:
                   - Basic: ellipse, oval, circle, box, polygon, triangle, diamond, point.
                   - Geometric: trapezium, parallelogram, house, pentagon, hexagon, octagon.
                   - Special: plaintext, star, cylinder, note, tab, folder, box3d, component.
            fontname: The name of the font to use for the graph elements (e.g., "Arial", "Verdana").
                   - For a full list, see the Graphviz documentation on node shapes.
        """
        self.agents_dir = agents_dir
        self.events_dir = events_dir
        self.postman_dir = postman_dir
        self.api_url = api_url.rstrip('/')
        self.interval = interval
        self.colors = colors or {}
        self.shapes = shapes or {}
        self.fontname = fontname
        self.postman_collection_generated = False  # Flag to ensure single generation

        if not self.agents_dir.exists() or not self.agents_dir.is_dir():
            raise ValueError(f"Agents directory not found or not a directory: {self.agents_dir}")
        if not self.events_dir.exists() or not self.events_dir.is_dir():
            raise ValueError(f"Events directory not found or not a directory: {self.events_dir}")

    @classmethod
    def from_config(cls, config: ConfigHelper, interval: Optional[int] = None) -> "EventFlowScanner":
        """
        Creates an EventFlowScanner instance from a ConfigHelper object.

        This factory method simplifies initialization by automatically extracting
        the required paths, API URL, and graph styling options from the validated configuration.

        Args:
            config: A fully initialized ConfigHelper instance.
            interval: Scan interval in seconds (None for one-shot mode).

        Returns:
            A configured instance of EventFlowScanner.
        """
        # Read port from root config
        port = config.config.get('port', 5555)
        api_url = f"http://localhost:{port}"

        return cls(
            agents_dir=config.get_agents_path(),
            events_dir=config.get_events_path(),
            postman_dir=config.get_postman_path(),
            api_url=api_url,
            interval=interval,
            colors=config.get_namespaces_colors(),
            shapes=config.get_namespaces_shapes(),
            fontname=config.get_graph_fontname()
        )

    def scan_once(self) -> Dict[str, bool]:
        """
        Perform a single scan, push to API, and generate Postman collection if configured.
        """
        print(f"[SCAN] Starting scan at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[SCAN] Agents directory: {self.agents_dir}")

        analyzer = EventFlowAnalyzer(self.agents_dir, self.events_dir)
        analyzer.analyze()

        events = analyzer.get_all_events()  # Now returns Set[NamespacedItem]
        agents = analyzer.get_all_agents()  # Now returns Set[NamespacedItem]
        print(f"[SCAN] Found {len(events)} events, {len(agents)} agents")

        namespaces = analyzer.get_all_namespaces()  # Get namespaces from both agents and events
        print(f"[SCAN] Found {len(namespaces)} namespaces: {sorted(namespaces)}")
        graph_types = ['complete', 'full-tree']
        results = {}

        for graph_type in graph_types:
            try:
                print(f"[SCAN] Generating {graph_type} graph...")
                dot_content = self._generate_dot(analyzer, graph_type)

                if dot_content:
                    total_connections = sum(len(s) for s in analyzer.event_to_subscribers.values()) + \
                                        sum(len(p) for p in analyzer.publications.values())

                    payload: Dict[str, Any] = {
                        'graph_type': graph_type,
                        'dot_content': dot_content,
                        'stats': {
                            'events': len(events),
                            'agents': len(agents),
                            'connections': total_connections,
                        },
                        'namespaces': list(namespaces)  # Always include namespaces key
                    }

                    # APPEND: Detect anomalies and add to payload (non-invasive)
                    try:
                        detector = AnomalyDetector(analyzer)
                        anomalies = detector.detect_all()
                        anomaly_summary = detector.get_anomaly_summary()

                        payload['anomalies'] = {
                            'summary': anomaly_summary,
                            'details': anomalies
                        }
                        print(f"[SCAN] Detected {anomaly_summary['total_anomalies']} anomalies")
                    except Exception as e:
                        print(f"[SCAN] Warning: Failed to detect anomalies: {e}")
                        # Continue without anomalies - no regression risk

                    success = self._push_to_api(payload)
                    results[graph_type] = success
                else:
                    print(f"[SCAN] Failed to generate {graph_type}")
                    results[graph_type] = False
            except Exception as e:
                print(f"[SCAN] Error processing {graph_type}: {e}")
                results[graph_type] = False

        return results

    def _generate_postman_collection(self, payload: Dict[str, Any]):
        """
        Generates a Postman collection file from a given payload.
        """
        collection_name = "Event Flow API.postman_collection.json"
        output_path = self.postman_dir / collection_name

        parsed_url = urlparse(f"{self.api_url}/api/graph")

        postman_json = {
            "info": {
                "name": "Event Flow Scanner API",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": [
                {
                    "name": "Push Graph Data",
                    "request": {
                        "method": "POST",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps(payload, indent=4)
                        },
                        "url": {
                            "raw": parsed_url.geturl(),
                            "protocol": parsed_url.scheme,
                            "host": [parsed_url.hostname],
                            "port": str(parsed_url.port),
                            "path": parsed_url.path.strip('/').split('/')
                        }
                    }
                }
            ]
        }

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(postman_json, f, indent=4)
            print(f"✅ Postman collection generated at: {output_path}")
        except IOError as e:
            print(f"❌ Failed to write Postman collection: {e}")

    def _push_to_api(self, payload: Dict) -> bool:
        """
        POST graph data to API and trigger Postman collection generation on success.
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
                print(f"[SCAN] ✅ Pushed {payload['graph_type']} successfully (Timestamp: {result.get('timestamp')})")

                if self.postman_dir and not self.postman_collection_generated:
                    self._generate_postman_collection(payload)
                    self.postman_collection_generated = True

                return True
            else:
                print(f"[SCAN] ❌ Failed to push {payload['graph_type']}: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"[SCAN] ❌ API request failed: {e}")
            return False

    def run_continuous(self) -> None:
        """
        Run scanner in continuous mode with configured interval
        """
        if self.interval is None:
            raise ValueError("Cannot run continuous mode without interval")

        print(f"[SCAN] Starting continuous scanner (interval: {self.interval}s)")
        print(f"[SCAN] API URL: {self.api_url}")
        print(f"[SCAN] Press Ctrl+C to stop")
        print()

        try:
            while True:
                self.scan_once()
                print(f"[SCAN] Sleeping for {self.interval} seconds...")
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\n[SCAN] Stopped by user")

    def _generate_dot(self, analyzer: EventFlowAnalyzer, graph_type: str) -> Optional[str]:
        """
        Generate DOT content for specified graph type using the graph_generators module.

        Args:
            analyzer: The EventFlowAnalyzer containing the parsed event flow data.
            graph_type: The type of graph to generate (e.g., 'complete', 'full-tree').

        Returns:
            The generated DOT content as a string, or None if generation fails.
        """
        try:
            generator = get_generator(
                graph_type=graph_type,
                colors=self.colors,
                shapes=self.shapes,
                fontname=self.fontname
            )
            return generator.generate(analyzer)
        except ValueError as e:
            print(f"[SCAN] Unknown graph type '{graph_type}': {e}")
            return None
        except Exception as e:
            print(f"[SCAN] Error generating DOT for {graph_type}: {e}")
            return None
