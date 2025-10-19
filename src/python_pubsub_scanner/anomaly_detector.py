"""
Anomaly Detection for Event Flow Analysis.

This module provides tools to detect potential issues in event-driven architectures:
- Orphaned events (never published or never subscribed)
- Circular dependencies between events
- Isolated agents (neither publishers nor subscribers)
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .analyze_event_flow import EventFlowAnalyzer, NamespacedItem


class AnomalyDetector:
    """
    Detects anomalies in event flow architecture.

    This class analyzes the event flow data to identify potential issues
    that may indicate architectural problems or bugs.
    """

    def __init__(self, analyzer: EventFlowAnalyzer):
        """
        Initialize the anomaly detector.

        Args:
            analyzer: An EventFlowAnalyzer instance with completed analysis.
        """
        self.analyzer = analyzer

    def detect_all(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Run all anomaly detections and return a comprehensive report.

        Returns:
            A dictionary with keys:
            - 'orphaned_events': List of events that are never published or never subscribed
            - 'cycles': List of detected circular dependencies
            - 'isolated_agents': List of agents with no connections
        """
        return {
            'orphaned_events': self.detect_orphaned_events(),
            'cycles': self.detect_cycles(),
            'isolated_agents': self.detect_isolated_agents(),
        }

    def detect_orphaned_events(self) -> List[Dict[str, str]]:
        """
        Detect events that are never published or never subscribed.

        An orphaned event is one that either:
        1. Has no publishers (never emitted) - potential dead code
        2. Has no subscribers (never consumed) - potential waste

        Returns:
            A list of dictionaries with keys:
            - 'event': The event name
            - 'namespace': The event namespace
            - 'type': 'never_published' or 'never_subscribed'
            - 'severity': 'warning' or 'info'
        """
        orphaned = []
        all_events = self.analyzer.get_all_events()

        for event in all_events:
            # Check if event is never published
            publishers = self.analyzer.event_to_publishers.get(event, [])
            if not publishers:
                orphaned.append({
                    'event': event.name,
                    'namespace': event.namespace,
                    'type': 'never_published',
                    'severity': 'warning',
                    'message': f"Event '{event.name}' is never published by any agent"
                })

            # Check if event is never subscribed
            subscribers = self.analyzer.event_to_subscribers.get(event, [])
            if not subscribers:
                orphaned.append({
                    'event': event.name,
                    'namespace': event.namespace,
                    'type': 'never_subscribed',
                    'severity': 'info',
                    'message': f"Event '{event.name}' has no subscribers"
                })

        return orphaned

    def detect_cycles(self) -> List[Dict[str, any]]:
        """
        Detect circular dependencies in the event flow.

        A cycle exists when Agent A publishes Event X, which is consumed by Agent B,
        which publishes Event Y, which is consumed by Agent A (directly or indirectly).

        Returns:
            A list of dictionaries with keys:
            - 'cycle': List of agent names forming the cycle
            - 'path': Detailed path showing agents and events
            - 'severity': 'warning'
        """
        cycles = []
        all_agents = self.analyzer.get_all_agents()

        # Build agent-to-agent graph
        # agent_graph[A] = set of agents that A can reach via published events
        agent_graph = defaultdict(set)

        for agent, published_events in self.analyzer.publications.items():
            for event in published_events:
                # Find who subscribes to this event
                subscribers = self.analyzer.event_to_subscribers.get(event, [])
                for subscriber in subscribers:
                    if subscriber != agent:  # Avoid self-loops
                        agent_graph[agent].add(subscriber)

        # DFS to detect cycles
        visited = set()
        rec_stack = set()
        path = []

        # noinspection PyShadowingNames
        def dfs(agent: NamespacedItem) -> bool:
            """DFS helper to detect cycles."""
            visited.add(agent)
            rec_stack.add(agent)
            path.append(agent)

            for neighbor in agent_graph.get(agent, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle_agents = path[cycle_start:]

                    # Build detailed path with events
                    detailed_path = []
                    for i in range(len(cycle_agents)):
                        current = cycle_agents[i]
                        next_agent = cycle_agents[(i + 1) % len(cycle_agents)]

                        # Find connecting event
                        connecting_events = []
                        for event in self.analyzer.publications.get(current, []):
                            if next_agent in self.analyzer.event_to_subscribers.get(event, []):
                                connecting_events.append(event.name)

                        detailed_path.append({
                            'agent': current.name,
                            'namespace': current.namespace,
                            'publishes': connecting_events
                        })

                    cycles.append({
                        'cycle': [a.name for a in cycle_agents],
                        'path': detailed_path,
                        'severity': 'warning',
                        'message': f"Circular dependency detected: {' -> '.join(a.name for a in cycle_agents)} -> {cycle_agents[0].name}"
                    })
                    return True

            path.pop()
            rec_stack.remove(agent)
            return False

        # Run DFS from each unvisited agent
        for agent in all_agents:
            if agent not in visited:
                path = []
                dfs(agent)

        return cycles

    def detect_isolated_agents(self) -> List[Dict[str, str]]:
        """
        Detect agents that have no connections (neither publishers nor subscribers).

        An isolated agent may indicate:
        - Dead code that should be removed
        - Configuration error
        - Agent that only performs internal operations

        Returns:
            A list of dictionaries with keys:
            - 'agent': The agent name
            - 'namespace': The agent namespace
            - 'severity': 'info'
        """
        isolated = []
        all_agents = self.analyzer.get_all_agents()

        for agent in all_agents:
            is_publisher = agent in self.analyzer.publications and len(self.analyzer.publications[agent]) > 0
            is_subscriber = agent in self.analyzer.subscriptions and len(self.analyzer.subscriptions[agent]) > 0

            if not is_publisher and not is_subscriber:
                isolated.append({
                    'agent': agent.name,
                    'namespace': agent.namespace,
                    'severity': 'info',
                    'message': f"Agent '{agent.name}' is isolated (no subscriptions or publications)"
                })

        return isolated

    def get_anomaly_summary(self) -> Dict[str, int]:
        """
        Get a summary count of all anomalies.

        Returns:
            A dictionary with counts for each anomaly type:
            - 'orphaned_events_count'
            - 'cycles_count'
            - 'isolated_agents_count'
            - 'total_anomalies'
        """
        anomalies = self.detect_all()

        counts = {
            'orphaned_events_count': len(anomalies['orphaned_events']),
            'cycles_count': len(anomalies['cycles']),
            'isolated_agents_count': len(anomalies['isolated_agents']),
        }
        counts['total_anomalies'] = sum(counts.values())

        return counts
