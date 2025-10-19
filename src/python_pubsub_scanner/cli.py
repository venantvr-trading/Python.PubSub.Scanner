"""
CLI entry point for Event Flow Scanner
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config_helper import ConfigHelper
from .scanner import EventFlowScanner


def main() -> None:
    """CLI entry point for scanner"""
    parser = argparse.ArgumentParser(
        description="Event Flow Scanner - Scan codebase and push graphs to API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using config file (recommended - includes colors and styling)
  pubsub-scanner --config event_flow_config.yaml --one-shot

  # Continuous scan with config (every 60 seconds)
  pubsub-scanner --config event_flow_config.yaml --interval 60

  # Manual mode: One-shot scan
  pubsub-scanner --agents-dir ./agents --api-url http://localhost:5555 --one-shot

  # Manual mode: With events directory for namespace info
  pubsub-scanner --agents-dir ./agents --events-dir ./events --one-shot

For more information: https://github.com/venantvr-trading/Python.PubSub.Scanner
        """
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file (event_flow_config.yaml)'
    )
    parser.add_argument(
        '--agents-dir',
        type=str,
        help='Path to agents directory (required if --config not provided)'
    )
    parser.add_argument(
        '--events-dir',
        type=str,
        help='Path to events directory (optional, for namespace info)'
    )
    parser.add_argument(
        '--api-url',
        type=str,
        default='http://localhost:5555',
        help='Base URL of event_flow API (default: http://localhost:5555)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        help='Scan interval in seconds (omit for one-shot mode)'
    )
    parser.add_argument(
        '--one-shot',
        action='store_true',
        help='Run once and exit (overrides --interval)'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.1.0'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode (show full tracebacks)'
    )

    args = parser.parse_args()

    # Determine mode. Default to one-shot if no mode is specified.
    is_continuous = args.interval is not None and not args.one_shot
    interval = args.interval if is_continuous else None

    if not is_continuous and not args.one_shot and args.interval is None:
        print("[SCAN] Info: Neither --one-shot nor --interval specified. Running a single scan.")

    try:
        # Create scanner from config or manual args
        if args.config:
            # Load from config file
            config_file = Path(args.config)
            config_file_name = config_file.name
            start_path = config_file.parent if config_file.parent != Path('.') else Path.cwd()
            config_helper = ConfigHelper(start_path=start_path, config_file_name=config_file_name)
            scanner = EventFlowScanner.from_config(config_helper, interval=interval)
        else:
            # Manual mode - require agents_dir
            if not args.agents_dir:
                print("Error: --agents-dir is required when --config is not provided", file=sys.stderr)
                sys.exit(1)

            agents_dir = Path(args.agents_dir)
            events_dir = Path(args.events_dir) if args.events_dir else None

            scanner = EventFlowScanner(
                agents_dir=agents_dir,
                events_dir=events_dir,
                api_url=args.api_url,
                interval=interval
            )

        # Run
        if is_continuous:
            scanner.run_continuous()
        else:
            results = scanner.scan_once()

            # Print summary and exit
            success_count = sum(1 for s in results.values() if s)
            total_count = len(results)

            print()
            print(f"[SCAN] Summary: {success_count}/{total_count} graphs pushed successfully")

            # Exit with appropriate code
            sys.exit(0 if success_count == total_count else 1)

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[SCAN] Interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
