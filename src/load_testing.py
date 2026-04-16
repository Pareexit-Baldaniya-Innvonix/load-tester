"""
Load Testing Module - Core library for load testing any URL.

Can be used as:
1. A library: from load_testing import run_load_test
2. Imported in other programs
3. Via FastAPI endpoints
"""

import os
import time
from pathlib import Path
from urllib.parse import urlparse


def get_api_user_class(HttpUser, task, between):
    """Helper to define the APIUser class dynamically."""

    class APIUser(HttpUser):
        """User class that simulates API requests to the target URL."""

        wait_time = between(0.5, 2.0)

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.target_path = getattr(self.environment, "target_path", "/")

        @task
        def get_request(self):
            """Make a GET request to the target endpoint."""
            with self.client.get(self.target_path, catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Got status code {response.status_code}")

    return APIUser


def export_csv(stats, filename):
    """Export statistics to CSV format."""
    with open(filename, "w") as f:
        # Write header
        f.write("Type,Name,Requests,Failures,Median,Average,Min,Max,Content-Type\n")

        # Write overall stats
        total = stats.total
        f.write(
            f"Total,,{total.num_requests},"
            f"{total.num_failures},"
            f"{total.get_response_time_percentile(0.5):.2f},"
            f"{total.avg_response_time:.2f},"
            f"{total.min_response_time:.2f},"
            f"{total.max_response_time:.2f},\n"
        )

        # Write per-endpoint stats
        for name, stat in stats.entries.items():
            if stat.num_requests > 0:
                f.write(
                    f"GET,{name},"
                    f"{stat.num_requests},"
                    f"{stat.num_failures},"
                    f"{stat.get_response_time_percentile(0.5):.2f},"
                    f"{stat.avg_response_time:.2f},"
                    f"{stat.min_response_time:.2f},"
                    f"{stat.max_response_time:.2f},\n"
                )


def create_html_report(env, filename, url, duration, num_users, ramp_rate):
    """Generate an HTML report with test results."""

    stats = env.stats

    # Calculate summary statistics
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    avg_response_time = stats.total.avg_response_time
    median_response_time = stats.total.get_response_time_percentile(0.5)
    p95_response_time = stats.total.get_response_time_percentile(0.95)
    p99_response_time = stats.total.get_response_time_percentile(0.99)

    success_rate = (
        ((total_requests - total_failures) / total_requests * 100)
        if total_requests > 0
        else 0
    )

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Load Test Report - {url}</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                min-height: 100vh;
                padding: 20px;
            }}

            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 8px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
                overflow: hidden;
            }}

            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }}

            .header h1 {{
                font-size: 2.5em;
                margin-bottom: 10px;
            }}

            .header p {{
                font-size: 1.1em;
                opacity: 0.9;
            }}

            .content {{
                padding: 40px;
            }}

            .test-params {{
                background: #f5f5f5;
                padding: 20px;
                border-radius: 6px;
                margin-bottom: 30px;
                border-left: 4px solid #667eea;
            }}

            .test-params h2 {{
                margin-bottom: 15px;
                color: #667eea;
            }}

            .param-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
            }}

            .param {{
                background: white;
                padding: 15px;
                border-radius: 4px;
                border: 1px solid #ddd;
            }}

            .param-label {{
                font-weight: bold;
                color: #667eea;
                margin-bottom: 5px;
            }}

            .param-value {{
                font-size: 1.2em;
                color: #333;
            }}

            .metrics {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}

            .metric-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 25px;
                border-radius: 6px;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
            }}

            .metric-card.success {{
                background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            }}

            .metric-card.warning {{
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            }}

            .metric-label {{
                font-size: 0.9em;
                opacity: 0.9;
                margin-bottom: 10px;
            }}

            .metric-value {{
                font-size: 2em;
                font-weight: bold;
            }}

            .metric-unit {{
                font-size: 0.8em;
                opacity: 0.8;
                margin-top: 5px;
            }}

            .stats-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}

            .stats-table thead {{
                background: #667eea;
                color: white;
            }}

            .stats-table th {{
                padding: 15px;
                text-align: left;
                font-weight: 600;
            }}

            .stats-table td {{
                padding: 12px 15px;
                border-bottom: 1px solid #eee;
            }}

            .stats-table tbody tr:hover {{
                background: #f9f9f9;
            }}

            h2 {{
                color: #333;
                margin: 30px 0 20px 0;
                font-size: 1.5em;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
            }}

            .response-times {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }}

            .response-time-item {{
                background: #f5f5f5;
                padding: 15px;
                border-radius: 4px;
                border-left: 4px solid #667eea;
            }}

            .response-time-label {{
                color: #666;
                font-size: 0.9em;
            }}

            .response-time-value {{
                font-size: 1.5em;
                font-weight: bold;
                color: #667eea;
                margin-top: 5px;
            }}

            .footer {{
                background: #f5f5f5;
                padding: 20px;
                text-align: center;
                color: #666;
                font-size: 0.9em;
                border-top: 1px solid #ddd;
            }}

            .failure-badge {{
                display: inline-block;
                background: #f5576c;
                color: white;
                padding: 5px 10px;
                border-radius: 20px;
                font-size: 0.9em;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Load Test Report</h1>
                <p>Comprehensive Performance Analysis</p>
            </div>

            <div class="content">
                <div class="test-params">
                    <h2>🎯 Test Parameters</h2>
                    <div class="param-grid">
                        <div class="param">
                            <div class="param-label">Target URL</div>
                            <div class="param-value" style="word-break: break-all; font-size: 0.95em;">{url}</div>
                        </div>
                        <div class="param">
                            <div class="param-label">Duration</div>
                            <div class="param-value">{duration}s</div>
                        </div>
                        <div class="param">
                            <div class="param-label">Max Users</div>
                            <div class="param-value">{num_users}</div>
                        </div>
                        <div class="param">
                            <div class="param-label">Ramp-up Rate</div>
                            <div class="param-value">{ramp_rate}/sec</div>
                        </div>
                    </div>
                </div>

                <h2>📈 Key Metrics</h2>
                <div class="metrics">
                    <div class="metric-card success">
                        <div class="metric-label">Total Requests</div>
                        <div class="metric-value">{total_requests}</div>
                    </div>
                    <div class="metric-card" style="background: linear-gradient(135deg, #38ef7d 0%, #11998e 100%);">
                        <div class="metric-label">Success Rate</div>
                        <div class="metric-value">{success_rate:.2f}%</div>
                    </div>
                    <div class="metric-card warning">
                        <div class="metric-label">Failed Requests</div>
                        <div class="metric-value">{total_failures}</div>
                    </div>
                    <div class="metric-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
                        <div class="metric-label">Avg Response Time</div>
                        <div class="metric-value">{avg_response_time:.2f}<span class="metric-unit">ms</div></span>
                    </div>
                </div>

                <h2>⏱️ Response Time Analysis</h2>
                <div class="response-times">
                    <div class="response-time-item">
                        <div class="response-time-label">Median (P50)</div>
                        <div class="response-time-value">{median_response_time:.2f} ms</div>
                    </div>
                    <div class="response-time-item">
                        <div class="response-time-label">95th Percentile (P95)</div>
                        <div class="response-time-value">{p95_response_time:.2f} ms</div>
                    </div>
                    <div class="response-time-item">
                        <div class="response-time-label">99th Percentile (P99)</div>
                        <div class="response-time-value">{p99_response_time:.2f} ms</div>
                    </div>
                </div>

                <h2>📋 Detailed Statistics by Endpoint</h2>
                <table class="stats-table">
                    <thead>
                        <tr>
                            <th>Endpoint</th>
                            <th>Requests</th>
                            <th>Failures</th>
                            <th>Avg (ms)</th>
                            <th>Min (ms)</th>
                            <th>Max (ms)</th>
                            <th>Median (ms)</th>
                        </tr>
                    </thead>
                    <tbody>
    """

    # Add per-endpoint statistics
    for name, stat in stats.entries.items():
        if stat.num_requests > 0:
            html_content += f"""
                        <tr>
                            <td><strong>{name}</strong></td>
                            <td>{stat.num_requests}</td>
                            <td><span class="failure-badge">{stat.num_failures}</td></span>
                            <td>{stat.avg_response_time:.2f}</td>
                            <td>{stat.min_response_time:.2f}</td>
                            <td>{stat.max_response_time:.2f}</td>
                            <td>{stat.get_response_time_percentile(0.5):.2f}</td>
                        </tr>
            """

    html_content += """
                    </tbody>
                </table>

            </div>

            <div class="footer">
                <p>Report generated by Locust Load Testing Tool</p>
                <p>For more information, visit: <a href="https://locust.io" style="color: #667eea;">https://locust.io</a></p>
            </div>
        </div>
    </body>
    </html>
    """

    with open(filename, "w") as f:
        f.write(html_content)


def run_load_test(
    url,
    duration=60,
    num_users=100,
    ramp_rate=10,
    csv_prefix=None,
    html_report=None,
    verbose=True,
    progress_callback=None,
):
    """
    Run a Locust load test with specified parameters.

    Args:
        url (str): Target URL to load test (e.g., http://example.com)
        duration (int): Test duration in seconds (default: 60)
        num_users (int): Maximum number of concurrent users (default: 100)
        ramp_rate (float): Number of users to spawn per second (default: 10)
        csv_prefix (str): Prefix for CSV files (default: locust_results)
        html_report (str): Path for HTML report (default: locust_report.html)
        verbose (bool): Print progress messages (default: True)
        progress_callback (callable): Function to call with progress updates (optional)

    Returns:
        dict: Dictionary containing test results and file paths

    Example:
        >>> from load_testing import run_load_test
        >>> results = run_load_test(
        ...     url="https://api.example.com",
        ...     duration=60,
        ...     num_users=50,
        ...     ramp_rate=5
        ... )
        >>> print(results['total_requests'])
    """

    # Set defaults
    if csv_prefix is None:
        csv_prefix = "locust_results"
    if html_report is None:
        html_report = "locust_report.html"

    # Get reports directory from environment or use default
    reports_dir = os.getenv("REPORTS_DIR", "./reports")
    reports_path = Path(reports_dir)

    # Create reports directory if it doesn't exist
    reports_path.mkdir(parents=True, exist_ok=True)

    # Add reports directory to file paths
    csv_prefix = str(reports_path / csv_prefix)
    html_report = str(reports_path / html_report)

    # Validate URL
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    # Extract path from URL if present
    parsed_url = urlparse(url)
    target_path = parsed_url.path if parsed_url.path else "/"

    # Reconstruct base URL (host)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    try:
        from gevent import monkey as _monkey

        if not _monkey.is_module_patched("socket"):
            _monkey.patch_all(ssl=False)
    except Exception:
        pass

    # Local import to avoid gevent monkey-patching on startup
    from locust import HttpUser, task, between
    from locust.env import Environment

    APIUser = get_api_user_class(HttpUser, task, between)

    # Create a minimal options object
    class MinimalOptions:
        headless = True
        loglevel = "INFO"

    # Create Locust environment with host and options
    env = Environment(user_classes=[APIUser], host=base_url)
    env.parsed_options = MinimalOptions()
    env.target_path = target_path

    # Create runner
    runner = env.create_local_runner()

    # Print test configuration
    if verbose:
        print(f"\n{'='*70}")
        print(f"🚀 LOAD TEST STARTING")
        print(f"{'='*70}")
        print(f"Target URL: {url}")
        print(f"Duration: {duration} seconds")
        print(f"Max Users: {num_users}")
        print(f"Ramp-up Rate: {ramp_rate} users/second")
        print(f"{'='*70}\n")

    try:
        # Start the test
        runner.start(user_count=num_users, spawn_rate=ramp_rate, wait=False)

        # Track the test duration
        start_time = time.time()
        last_print_time = start_time

        # Keep the test running for the specified duration
        while time.time() - start_time < duration:
            # Print progress every 2 seconds
            current_time = time.time()
            if current_time - last_print_time >= 2:
                elapsed = int(current_time - start_time)
                current_users = runner.user_count
                requests_per_sec = env.stats.total.total_rps

                progress_msg = f"⏱️  {elapsed}s elapsed | 👥 {current_users} users | 📊 {requests_per_sec:.2f} req/s"

                if verbose:
                    print(progress_msg)

                # Call progress callback if provided
                if progress_callback:
                    progress_callback(
                        {
                            "elapsed": elapsed,
                            "users": current_users,
                            "rps": requests_per_sec,
                        }
                    )

                last_print_time = current_time

            time.sleep(0.1)

        # Stop the test
        runner.stop()
        runner.quit()

        if verbose:
            print(f"\n{'='*70}")
            print(f"✅ LOAD TEST COMPLETED")
            print(f"{'='*70}\n")

        # Generate reports
        if verbose:
            print(f"📊 Generating reports...")

        # Generate CSV stats
        stats_file = f"{csv_prefix}_stats.csv"
        export_csv(env.stats, stats_file)
        if verbose:
            print(f"✓ CSV stats saved to: {stats_file}")

        # Create HTML report
        create_html_report(env, html_report, url, duration, num_users, ramp_rate)
        if verbose:
            print(f"✓ HTML report saved to: {html_report}")

        # Prepare results
        total_requests = env.stats.total.num_requests
        total_failures = env.stats.total.num_failures
        avg_response_time = env.stats.total.avg_response_time
        median_response_time = env.stats.total.get_response_time_percentile(0.5)
        p95_response_time = env.stats.total.get_response_time_percentile(0.95)
        p99_response_time = env.stats.total.get_response_time_percentile(0.99)
        success_rate = (
            ((total_requests - total_failures) / total_requests * 100)
            if total_requests > 0
            else 0
        )

        results = {
            "total_requests": total_requests,
            "total_failures": total_failures,
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "median_response_time": median_response_time,
            "p95_response_time": p95_response_time,
            "p99_response_time": p99_response_time,
            "csv_file": stats_file,
            "html_report": html_report,
            "url": url,
            "duration": duration,
            "num_users": num_users,
            "ramp_rate": ramp_rate,
        }

        return results

    except KeyboardInterrupt:
        if verbose:
            print("\n⚠️  Test interrupted by user")
        try:
            runner.stop()
            runner.quit()
        except:
            pass
        raise
    except Exception as e:
        if verbose:
            print(f"\n❌ Error during load test: {e}")
            import traceback

            traceback.print_exc()
        raise
    finally:
        try:
            env.stats.clear_all()
        except:
            pass
