"""
CLI entry point for Event Flow Scanner
"""
import argparse
import sys
from pathlib import Path

from .scanner import EventFlowScanner


def main():
    """CLI entry point for scanner"""
    parser = argparse.ArgumentParser(
        description="Event Flow Scanner - Scan codebase and push graphs to API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # One-shot scan
  pubsub-scanner --agents-dir ./agents --api-url http://localhost:5555 --one-shot

  # Continuous scan (every 60 seconds)
  pubsub-scanner --agents-dir ./agents --interval 60

  # With events directory for namespace info
  pubsub-scanner --agents-dir ./agents --events-dir ./events --one-shot

For more information: https://github.com/venantvr-trading/Python.PubSub.Scanner
        """
    )

    parser.add_argument(
        '--agents-dir',
        type=str,
        required=True,
        help='Path to agents directory (required)'
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

    # Parse paths
    agents_dir = Path(args.agents_dir)
    events_dir = Path(args.events_dir) if args.events_dir else None

    # Determine mode. Default to one-shot if no mode is specified.
    is_continuous = args.interval is not None and not args.one_shot
    interval = args.interval if is_continuous else None

    if not is_continuous and not args.one_shot and args.interval is None:
        print("[SCAN] Info: Neither --one-shot nor --interval specified. Running a single scan.")


    try:
        # Create scanner
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
