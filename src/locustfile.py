"""
CLI entry point for the load testing tool.

This script provides a command-line interface to the load_testing module.
For programmatic usage, import directly from load_testing module.

Usage:
    python locustfile.py -u http://example.com
    python locustfile.py -u http://example.com -d 60 -n 50 -r 5
"""

import sys
import argparse
from load_testing import run_load_test


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Locust Load Testing Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python locustfile.py --url http://example.com
  python locustfile.py -u http://example.com -d 60 -n 50 -r 5
  python locustfile.py -u https://api.example.com/endpoint -d 120 -n 50 -r 5 -o custom_report.html
        """
    )

    parser.add_argument(
        '--url', '-u',
        required=True,
        help='Target URL for load testing (e.g., http://example.com)'
    )
    parser.add_argument(
        '--duration', '-d',
        type=int,
        default=60,
        help='Test duration in seconds (default: 60)'
    )
    parser.add_argument(
        '--users', '-n',
        type=int,
        default=100,
        help='Maximum number of concurrent users (default: 100)'
    )
    parser.add_argument(
        '--ramp-rate', '-r',
        type=float,
        default=10,
        help='Number of users to spawn per second (default: 10)'
    )
    parser.add_argument(
        '--csv-prefix',
        default='locust_results',
        help='Prefix for CSV files (default: locust_results)'
    )
    parser.add_argument(
        '--output', '-o',
        default='locust_report.html',
        help='Output HTML report filename (default: locust_report.html)'
    )

    args = parser.parse_args()

    try:
        results = run_load_test(
            url=args.url,
            duration=args.duration,
            num_users=args.users,
            ramp_rate=args.ramp_rate,
            csv_prefix=args.csv_prefix,
            html_report=args.output,
            verbose=True
        )
        print("\n✅ Load test completed successfully!")
        return 0
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Load test failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
