from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from python_pubsub_scanner.analyze_event_flow import NamespacedItem
from python_pubsub_scanner.anomaly_detector import AnomalyDetector


class TestAnomalyDetector(unittest.TestCase):
    """
    Tests for the AnomalyDetector class.
    """

    def setUp(self):
        """Set up mock analyzer for testing."""
        self.mock_analyzer = MagicMock()

    def test_detect_orphaned_event_never_published(self):
        """Test detection of events that are never published."""
        # Create test events
        event_orphan = NamespacedItem(name="OrphanEvent", namespace="test")
        event_normal = NamespacedItem(name="NormalEvent", namespace="test")
        agent = NamespacedItem(name="TestAgent", namespace="test")

        # Setup: OrphanEvent has no publishers, NormalEvent has publishers
        self.mock_analyzer.get_all_events.return_value = {event_orphan, event_normal}
        self.mock_analyzer.event_to_publishers = {
            event_normal: [agent]
            # event_orphan is missing - never published
        }
        self.mock_analyzer.event_to_subscribers = {
            event_orphan: [agent],
            event_normal: [agent]
        }

        detector = AnomalyDetector(self.mock_analyzer)
        orphaned = detector.detect_orphaned_events()

        # Should find OrphanEvent as never published
        never_published = [o for o in orphaned if o['type'] == 'never_published']
        self.assertEqual(len(never_published), 1)
        self.assertEqual(never_published[0]['event'], 'OrphanEvent')
        self.assertEqual(never_published[0]['severity'], 'warning')

    def test_detect_orphaned_event_never_subscribed(self):
        """Test detection of events that are never subscribed."""
        # Create test events
        event_orphan = NamespacedItem(name="UnsubscribedEvent", namespace="test")
        event_normal = NamespacedItem(name="NormalEvent", namespace="test")
        agent = NamespacedItem(name="TestAgent", namespace="test")

        # Setup: UnsubscribedEvent has no subscribers
        self.mock_analyzer.get_all_events.return_value = {event_orphan, event_normal}
        self.mock_analyzer.event_to_publishers = {
            event_orphan: [agent],
            event_normal: [agent]
        }
        self.mock_analyzer.event_to_subscribers = {
            event_normal: [agent]
            # event_orphan is missing - never subscribed
        }

        detector = AnomalyDetector(self.mock_analyzer)
        orphaned = detector.detect_orphaned_events()

        # Should find UnsubscribedEvent as never subscribed
        never_subscribed = [o for o in orphaned if o['type'] == 'never_subscribed']
        self.assertEqual(len(never_subscribed), 1)
        self.assertEqual(never_subscribed[0]['event'], 'UnsubscribedEvent')
        self.assertEqual(never_subscribed[0]['severity'], 'info')

    def test_detect_no_orphaned_events(self):
        """Test that no orphaned events are detected when all events are connected."""
        event = NamespacedItem(name="Event", namespace="test")
        agent_pub = NamespacedItem(name="Publisher", namespace="test")
        agent_sub = NamespacedItem(name="Subscriber", namespace="test")

        self.mock_analyzer.get_all_events.return_value = {event}
        self.mock_analyzer.event_to_publishers = {event: [agent_pub]}
        self.mock_analyzer.event_to_subscribers = {event: [agent_sub]}

        detector = AnomalyDetector(self.mock_analyzer)
        orphaned = detector.detect_orphaned_events()

        self.assertEqual(len(orphaned), 0)

    def test_detect_isolated_agents(self):
        """Test detection of agents with no connections."""
        agent_isolated = NamespacedItem(name="IsolatedAgent", namespace="test")
        agent_publisher = NamespacedItem(name="PublisherAgent", namespace="test")
        agent_subscriber = NamespacedItem(name="SubscriberAgent", namespace="test")
        event = NamespacedItem(name="Event", namespace="test")

        self.mock_analyzer.get_all_agents.return_value = {
            agent_isolated,
            agent_publisher,
            agent_subscriber
        }
        self.mock_analyzer.publications = {
            agent_publisher: [event]
        }
        self.mock_analyzer.subscriptions = {
            agent_subscriber: [event]
        }

        detector = AnomalyDetector(self.mock_analyzer)
        isolated = detector.detect_isolated_agents()

        # Should find IsolatedAgent
        self.assertEqual(len(isolated), 1)
        self.assertEqual(isolated[0]['agent'], 'IsolatedAgent')
        self.assertEqual(isolated[0]['severity'], 'info')

    def test_detect_no_isolated_agents(self):
        """Test that no isolated agents are detected when all are connected."""
        agent_pub = NamespacedItem(name="Publisher", namespace="test")
        agent_sub = NamespacedItem(name="Subscriber", namespace="test")
        event = NamespacedItem(name="Event", namespace="test")

        self.mock_analyzer.get_all_agents.return_value = {agent_pub, agent_sub}
        self.mock_analyzer.publications = {agent_pub: [event]}
        self.mock_analyzer.subscriptions = {agent_sub: [event]}

        detector = AnomalyDetector(self.mock_analyzer)
        isolated = detector.detect_isolated_agents()

        self.assertEqual(len(isolated), 0)

    def test_detect_simple_cycle(self):
        """Test detection of a simple circular dependency: A -> B -> A."""
        agent_a = NamespacedItem(name="AgentA", namespace="test")
        agent_b = NamespacedItem(name="AgentB", namespace="test")
        event_x = NamespacedItem(name="EventX", namespace="test")
        event_y = NamespacedItem(name="EventY", namespace="test")

        # AgentA publishes EventX, AgentB subscribes to EventX
        # AgentB publishes EventY, AgentA subscribes to EventY
        # This creates a cycle: AgentA -> EventX -> AgentB -> EventY -> AgentA

        self.mock_analyzer.get_all_agents.return_value = {agent_a, agent_b}
        self.mock_analyzer.publications = {
            agent_a: [event_x],
            agent_b: [event_y]
        }
        self.mock_analyzer.subscriptions = {
            agent_a: [event_y],
            agent_b: [event_x]
        }
        self.mock_analyzer.event_to_subscribers = {
            event_x: [agent_b],
            event_y: [agent_a]
        }

        detector = AnomalyDetector(self.mock_analyzer)
        cycles = detector.detect_cycles()

        # Should detect at least one cycle
        self.assertGreater(len(cycles), 0)
        cycle = cycles[0]
        self.assertEqual(cycle['severity'], 'warning')
        self.assertIn('AgentA', cycle['cycle'])
        self.assertIn('AgentB', cycle['cycle'])

    def test_detect_no_cycles(self):
        """Test that no cycles are detected in a linear flow."""
        agent_a = NamespacedItem(name="AgentA", namespace="test")
        agent_b = NamespacedItem(name="AgentB", namespace="test")
        event = NamespacedItem(name="Event", namespace="test")

        # Linear: AgentA -> Event -> AgentB (no cycle)
        self.mock_analyzer.get_all_agents.return_value = {agent_a, agent_b}
        self.mock_analyzer.publications = {agent_a: [event]}
        self.mock_analyzer.subscriptions = {agent_b: [event]}
        self.mock_analyzer.event_to_subscribers = {event: [agent_b]}

        detector = AnomalyDetector(self.mock_analyzer)
        cycles = detector.detect_cycles()

        self.assertEqual(len(cycles), 0)

    def test_detect_all(self):
        """Test that detect_all returns all anomaly types."""
        # Create a scenario with all types of anomalies
        agent_isolated = NamespacedItem(name="Isolated", namespace="test")
        agent_a = NamespacedItem(name="AgentA", namespace="test")
        agent_b = NamespacedItem(name="AgentB", namespace="test")
        event_orphan = NamespacedItem(name="OrphanEvent", namespace="test")
        event_x = NamespacedItem(name="EventX", namespace="test")
        event_y = NamespacedItem(name="EventY", namespace="test")

        self.mock_analyzer.get_all_agents.return_value = {agent_isolated, agent_a, agent_b}
        self.mock_analyzer.get_all_events.return_value = {event_orphan, event_x, event_y}

        # Isolated agent
        self.mock_analyzer.publications = {
            agent_a: [event_x],
            agent_b: [event_y]
        }
        self.mock_analyzer.subscriptions = {
            agent_a: [event_y],
            agent_b: [event_x]
        }

        # Orphan event (never published, never subscribed)
        self.mock_analyzer.event_to_publishers = {
            event_x: [agent_a],
            event_y: [agent_b]
        }
        self.mock_analyzer.event_to_subscribers = {
            event_x: [agent_b],
            event_y: [agent_a]
        }

        detector = AnomalyDetector(self.mock_analyzer)
        all_anomalies = detector.detect_all()

        # Should have all three keys
        self.assertIn('orphaned_events', all_anomalies)
        self.assertIn('cycles', all_anomalies)
        self.assertIn('isolated_agents', all_anomalies)

        # Should detect at least one of each type
        self.assertGreater(len(all_anomalies['orphaned_events']), 0)
        self.assertGreater(len(all_anomalies['cycles']), 0)
        self.assertGreater(len(all_anomalies['isolated_agents']), 0)

    def test_get_anomaly_summary(self):
        """Test that get_anomaly_summary returns correct counts."""
        agent = NamespacedItem(name="Agent", namespace="test")
        event_orphan = NamespacedItem(name="OrphanEvent", namespace="test")

        self.mock_analyzer.get_all_agents.return_value = {agent}
        self.mock_analyzer.get_all_events.return_value = {event_orphan}
        self.mock_analyzer.publications = {}
        self.mock_analyzer.subscriptions = {}
        self.mock_analyzer.event_to_publishers = {}
        self.mock_analyzer.event_to_subscribers = {}

        detector = AnomalyDetector(self.mock_analyzer)
        summary = detector.get_anomaly_summary()

        # Should have all count keys
        self.assertIn('orphaned_events_count', summary)
        self.assertIn('cycles_count', summary)
        self.assertIn('isolated_agents_count', summary)
        self.assertIn('total_anomalies', summary)

        # Should have at least one orphaned event and one isolated agent
        self.assertGreater(summary['orphaned_events_count'], 0)
        self.assertGreater(summary['isolated_agents_count'], 0)
        self.assertGreater(summary['total_anomalies'], 0)


if __name__ == '__main__':
    unittest.main()
