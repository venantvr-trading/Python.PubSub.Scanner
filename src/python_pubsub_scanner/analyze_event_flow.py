"""
Event Flow Analyzer

Parses all agents to extract event subscriptions and publications,
then generates a visual graph of the event flow.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set


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

    def __init__(self, agents_dir: Path):
        """
        Initialize analyzer

        Args:
            agents_dir: Path to directory containing agent files
        """
        self.agents_dir = agents_dir
        self.subscriptions: Dict[str, List[str]] = defaultdict(list)
        self.publications: Dict[str, List[str]] = defaultdict(list)
        self.event_to_subscribers: Dict[str, List[str]] = defaultdict(list)
        self.event_to_publishers: Dict[str, List[str]] = defaultdict(list)

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

        # Find subscriptions: self.service_bus.subscribe(EventName.__name__, ...)
        subscribe_pattern = r'self\.service_bus\.subscribe\(([A-Za-z_]+)\.__name__'
        for match in re.finditer(subscribe_pattern, content):
            event_name = match.group(1)
            self.subscriptions[agent_name].append(event_name)
            self.event_to_subscribers[event_name].append(agent_name)

        # Find publications: self.service_bus.publish(EventName.__name__, ...)
        publish_pattern = r'self\.service_bus\.publish\(([A-Za-z_]+)\.__name__'
        for match in re.finditer(publish_pattern, content):
            event_name = match.group(1)
            self.publications[agent_name].append(event_name)
            self.event_to_publishers[event_name].append(agent_name)

    def get_all_events(self) -> Set[str]:
        """
        Get all unique events across all agents

        Returns:
            Set of event names
        """
        events = set()
        events.update(self.event_to_subscribers.keys())
        events.update(self.event_to_publishers.keys())
        return events

    def get_event_chains(self) -> List[List[str]]:
        """
        Build event chains (sequences of events)

        Returns:
            List of event chains, where each chain is a list of event names
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

    def _build_chain(self, event: str, visited: Set[str]) -> List[str]:
        """
        Recursively build an event chain

        Args:
            event: Starting event
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
            lines.append(f'    "{event}" [style=filled, fillcolor=lightblue, shape=ellipse];')

        lines.append('')
        lines.append('    // Agents')
        for agent in sorted(agents):
            lines.append(f'    "{agent}" [style=filled, fillcolor=lightyellow];')

        lines.append('')
        lines.append('    // Event Flow')

        # Add edges
        for event, subscribers in sorted(self.event_to_subscribers.items()):
            for subscriber in subscribers:
                lines.append(f'    "{event}" -> "{subscriber}";')

        for agent, publications in sorted(self.publications.items()):
            for event in publications:
                lines.append(f'    "{agent}" -> "{event}";')

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

            print(f"\n📌 {event}")

            if publishers:
                print(f"   Published by: {', '.join(sorted(publishers))}")
            else:
                print(f"   Published by: [EXTERNAL/ORCHESTRATOR]")

            if subscribers:
                print(f"   Consumed by:  {', '.join(sorted(subscribers))}")
            else:
                print(f"   Consumed by:  [NO SUBSCRIBERS]")

        print()
        print("-" * 80)
        print("AGENT EVENT MATRIX")
        print("-" * 80)

        for agent in sorted(agents):
            subscribed = self.subscriptions.get(agent, [])
            published = self.publications.get(agent, [])

            print(f"\n🤖 {agent}")
            if subscribed:
                print(f"   Listens to: {', '.join(sorted(subscribed))}")
            if published:
                print(f"   Publishes:  {', '.join(sorted(published))}")
