"""
Event Flow Analyzer

Parses all agents to extract event subscriptions and publications,
then generates a visual graph of the event flow.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set


@dataclass
class NamespacedItem:
    """
    Represents an item (event or agent) with its name and namespace.

    Attributes:
        name: The class name (e.g., "UserCreated")
        namespace: The namespace/module (e.g., "user_service")
    """
    name: str
    namespace: str

    def __hash__(self):
        return hash((self.name, self.namespace))

    def __eq__(self, other):
        if isinstance(other, NamespacedItem):
            return self.name == other.name and self.namespace == other.namespace
        return False

    def __lt__(self, other):
        if isinstance(other, NamespacedItem):
            return (self.namespace, self.name) < (other.namespace, other.name)
        return NotImplemented


class EventFlowAnalyzer:
    """
    Analyzes agent files to extract event subscriptions and publications

    Attributes:
        agents_dir: Directory containing agent Python files
        subscriptions: Mapping of agent -> list of subscribed events
        publications: Mapping of agent -> list of published events
        event_to_subscribers: Mapping of event -> list of subscriber agents
        event_to_publishers: Mapping of event -> list of publisher agents
    """

    def __init__(self, agents_dir: Path, events_dir: Path = None):
        """
        Initialize analyzer

        Args:
            agents_dir: Path to directory containing agent files
            events_dir: Path to directory containing event files (optional)
        """
        self.agents_dir = agents_dir
        self.events_dir = events_dir
        self.subscriptions: Dict[NamespacedItem, List[NamespacedItem]] = defaultdict(list)
        self.publications: Dict[NamespacedItem, List[NamespacedItem]] = defaultdict(list)
        self.event_to_subscribers: Dict[NamespacedItem, List[NamespacedItem]] = defaultdict(list)
        self.event_to_publishers: Dict[NamespacedItem, List[NamespacedItem]] = defaultdict(list)

        # Build mapping of event class names to their directory namespaces
        self.event_class_to_namespace: Dict[str, str] = {}
        if events_dir and events_dir.exists():
            self._scan_events_directory()

    def _scan_events_directory(self) -> None:
        """
        Scan the events directory to build a mapping of class names to their namespace (directory name).

        For example, if events_dir contains:
            events/user_service/UserCreated.py -> maps "UserCreated" to "user_service"
            events/order_service/OrderPlaced.py -> maps "OrderPlaced" to "order_service"
        """
        # Pattern to extract class names from Python files
        class_pattern = re.compile(r'class\s+([A-Z][A-Za-z0-9_]*)\s*[:\(]')

        for namespace_dir in self.events_dir.iterdir():
            if not namespace_dir.is_dir() or namespace_dir.name.startswith('__'):
                continue

            namespace = namespace_dir.name

            # Scan all Python files in this namespace directory
            for event_file in namespace_dir.glob("*.py"):
                if event_file.name.startswith("__"):
                    continue

                try:
                    content = event_file.read_text()
                    # Find all class definitions in the file
                    for match in class_pattern.finditer(content):
                        class_name = match.group(1)
                        self.event_class_to_namespace[class_name] = namespace
                except Exception as e:
                    # Skip files that can't be read
                    pass

    def analyze(self) -> None:
        """Analyze all agent files in the agents directory"""
        agent_files = list(self.agents_dir.glob("*.py"))

        for agent_file in agent_files:
            if agent_file.name.startswith("__"):
                continue

            agent_name = agent_file.stem
            self._analyze_file(agent_file, agent_name)

    def _analyze_file(self, file_path: Path, agent_name: str) -> None:
        """
        Analyze a single agent file to extract event patterns

        Args:
            file_path: Path to the agent file
            agent_name: Name of the agent
        """
        content = file_path.read_text()

        # First pass: collect published events to determine agent namespace
        published_events = []
        publish_pattern = r'self\.service_bus\.publish\(([A-Za-z_]+)\.__name__'
        for match in re.finditer(publish_pattern, content):
            event_class_name = match.group(1)
            event_namespace = self.event_class_to_namespace.get(event_class_name, 'default')
            published_events.append((event_class_name, event_namespace))

        # Determine agent namespace from most common published event namespace
        # (excluding 'default' to avoid contamination)
        agent_namespace = 'default'
        if published_events:
            namespace_counts = Counter(ns for _, ns in published_events if ns != 'default')
            if namespace_counts:
                agent_namespace = namespace_counts.most_common(1)[0][0]

        agent_item = NamespacedItem(name=agent_name, namespace=agent_namespace)

        # Find subscriptions: self.service_bus.subscribe(EventName.__name__, ...)
        subscribe_pattern = r'self\.service_bus\.subscribe\(([A-Za-z_]+)\.__name__'
        for match in re.finditer(subscribe_pattern, content):
            event_class_name = match.group(1)
            event_namespace = self.event_class_to_namespace.get(event_class_name, 'default')
            event_item = NamespacedItem(name=event_class_name, namespace=event_namespace)

            self.subscriptions[agent_item].append(event_item)
            self.event_to_subscribers[event_item].append(agent_item)

        # Add publications (already collected above)
        for event_class_name, event_namespace in published_events:
            event_item = NamespacedItem(name=event_class_name, namespace=event_namespace)
            self.publications[agent_item].append(event_item)
            self.event_to_publishers[event_item].append(agent_item)

    def get_all_events(self) -> Set[NamespacedItem]:
        """
        Get all unique events across all agents

        Returns:
            Set of NamespacedItem objects representing events
        """
        events = set()
        events.update(self.event_to_subscribers.keys())
        events.update(self.event_to_publishers.keys())
        return events

    def get_all_agents(self) -> Set[NamespacedItem]:
        """
        Get all unique agents

        Returns:
            Set of NamespacedItem objects representing agents
        """
        return set(self.subscriptions.keys()) | set(self.publications.keys())

    def get_all_namespaces(self) -> Set[str]:
        """
        Get all unique namespaces from both agents and events

        Returns:
            Set of namespace strings
        """
        namespaces = set()

        # Collect event namespaces
        for event in self.get_all_events():
            namespaces.add(event.namespace)

        # Collect agent namespaces
        for agent in self.get_all_agents():
            namespaces.add(agent.namespace)

        return namespaces

    def get_event_chains(self) -> List[List[NamespacedItem]]:
        """
        Build event chains (sequences of events)

        Returns:
            List of event chains, where each chain is a list of NamespacedItem
        """
        chains = []
        visited = set()

        # Find entry point events (published but never consumed by agents)
        entry_events = []
        for event in self.event_to_publishers.keys():
            if event not in self.event_to_subscribers:
                entry_events.append(event)

        # Build chains starting from entry events
        for entry_event in entry_events:
            chain = self._build_chain(entry_event, visited)
            if chain:
                chains.append(chain)

        return chains

    def _build_chain(self, event: NamespacedItem, visited: Set[NamespacedItem]) -> List[NamespacedItem]:
        """
        Recursively build an event chain

        Args:
            event: Starting event (NamespacedItem)
            visited: Set of already visited events

        Returns:
            List of events in the chain
        """
        if event in visited:
            return []

        visited.add(event)
        chain = [event]

        # Find agents that subscribe to this event
        subscribers = self.event_to_subscribers.get(event, [])

        # For each subscriber, find what events they publish
        for subscriber in subscribers:
            published_events = self.publications.get(subscriber, [])
            for published_event in published_events:
                sub_chain = self._build_chain(published_event, visited)
                if sub_chain:
                    chain.extend(sub_chain)

        return chain

    def generate_graphviz(self) -> str:
        """
        Generate Graphviz DOT format representation

        Returns:
            DOT format string
        """
        lines = ['digraph EventFlow {',
                 '    rankdir=LR;',
                 '    node [shape=box];',
                 '']

        events = self.get_all_events()
        agents = set(self.subscriptions.keys()) | set(self.publications.keys())

        # Define event nodes
        lines.append('    // Events')
        for event in sorted(events):
            lines.append(f'    "{event.name}" [style=filled, fillcolor=lightblue, shape=ellipse, class="namespace-{event.namespace}"];')

        lines.append('')
        lines.append('    // Agents')
        for agent in sorted(agents):
            lines.append(f'    "{agent.name}" [style=filled, fillcolor=lightyellow, class="namespace-{agent.namespace}"];')

        lines.append('')
        lines.append('    // Event Flow')

        # Add edges
        for event, subscribers in sorted(self.event_to_subscribers.items()):
            for subscriber in subscribers:
                lines.append(f'    "{event.name}" -> "{subscriber.name}";')

        for agent, publications in sorted(self.publications.items()):
            for event in publications:
                lines.append(f'    "{agent.name}" -> "{event.name}";')

        lines.append('}')
        return '\n'.join(lines)

    def print_summary(self) -> None:
        """Print a text summary of the event flow to console"""
        print("=" * 80)
        print("EVENT FLOW ANALYSIS")
        print("=" * 80)
        print()

        events = self.get_all_events()
        agents = set(self.subscriptions.keys()) | set(self.publications.keys())

        print(f"Total Events: {len(events)}")
        print(f"Total Agents: {len(agents)}")
        print()

        print("-" * 80)
        print("EVENTS → SUBSCRIBERS → PUBLISHERS")
        print("-" * 80)

        for event in sorted(events):
            subscribers = self.event_to_subscribers.get(event, [])
            publishers = self.event_to_publishers.get(event, [])

            print(f"\n📌 {event.name} (namespace: {event.namespace})")

            if publishers:
                print(f"   Published by: {', '.join(sorted(p.name for p in publishers))}")
            else:
                print(f"   Published by: [EXTERNAL/ORCHESTRATOR]")

            if subscribers:
                print(f"   Consumed by:  {', '.join(sorted(s.name for s in subscribers))}")
            else:
                print(f"   Consumed by:  [NO SUBSCRIBERS]")

        print()
        print("-" * 80)
        print("AGENT EVENT MATRIX")
        print("-" * 80)

        for agent in sorted(agents):
            subscribed = self.subscriptions.get(agent, [])
            published = self.publications.get(agent, [])

            print(f"\n🤖 {agent.name} (namespace: {agent.namespace})")
            if subscribed:
                print(f"   Listens to: {', '.join(sorted(e.name for e in subscribed))}")
            if published:
                print(f"   Publishes:  {', '.join(sorted(e.name for e in published))}")
