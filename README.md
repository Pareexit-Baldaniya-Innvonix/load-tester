# Locust Load Testing

A modern load testing tool built with [Locust](https://locust.io) and [FastAPI](https://fastapi.tiangolo.com/). Test any website or API endpoint through a web dashboard, REST API, or command line -- with beautiful HTML reports, real-time progress tracking, and persistent test history.

## Features

- Load test any URL (websites or API endpoints)
- Web UI dashboard with real-time progress and test history
- REST API for automated/remote testing
- CLI mode for quick terminal-based testing
- Configurable concurrent users, ramp-up rate, and duration
- HTML reports with response time percentiles (P50, P95, P99)
- CSV export for detailed analysis
- SQLite database for persistent test history and statistics
- Per-endpoint statistics breakdown

## Prerequisites

- Python 3.12+
- Pipenv

## Quick Start

### 1. Install dependencies and activate the environment

```bash
pipenv install
pipenv shell
```

### 2. Run the web dashboard

```bash
python -m src.main
```

Open [http://localhost:8000](http://localhost:8000) in your browser to access the dashboard.

API documentation is available at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 3. Or run from the command line

```bash
# Basic test with defaults (120s, 100 users, 10 ramp-rate)
python src/locustfile.py --url http://example.com

# Custom parameters
python src/locustfile.py --url http://example.com --duration 60 --users 50 --ramp-rate 5
```

## Usage

### Web Dashboard

The dashboard at [http://localhost:8000](http://localhost:8000) provides:

- **Test Form** -- configure target URL, duration, concurrent users, ramp rate, and report name
- **Quick Stats** -- live counters for total, running, completed, and failed tests
- **Progress Tracking** -- real-time progress bar with elapsed time for the current test
- **Test History** -- filterable table of all test runs with status badges, success rate, response times, and download links for reports

### REST API

Start a load test programmatically:

```bash
curl -X POST http://localhost:8000/load-test \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://example.com",
    "duration": 60,
    "num_users": 100,
    "ramp_rate": 10
  }'
```

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web UI dashboard |
| `/api` | GET | API information |
| `/load-test` | POST | Start a new load test |
| `/load-test/{test_id}` | GET | Get test status and results |
| `/load-test/{test_id}/report` | GET | Download HTML report |
| `/load-test/{test_id}/csv` | GET | Download CSV results |
| `/tests` | GET | List all tests |
| `/db/tests` | GET | List all tests from database (with pagination) |
| `/db/tests/{test_id}` | GET | Get detailed test record |
| `/db/stats` | GET | Overall test statistics |
| `/db/tests/{test_id}` | DELETE | Delete a test record |

### CLI Arguments

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--url` | `-u` | *required* | Target URL |
| `--duration` | `-d` | 120 | Test duration in seconds |
| `--users` | `-n` | 100 | Maximum concurrent users |
| `--ramp-rate` | `-r` | 10 | Users spawned per second |
| `--csv-prefix` | | `locust_results` | Prefix for CSV output files |
| `--output` | `-o` | `locust_report.html` | HTML report filename |

### Python Module

```python
from src.load_testing import run_load_test

results = run_load_test(
    url="http://example.com",
    duration=120,
    num_users=100,
    ramp_rate=10,
)

print(f"Success rate: {results['success_rate']}%")
print(f"Avg response time: {results['avg_response_time']}ms")
```

## Project Structure

```
load-tester/
├── src/
│   ├── main.py              # FastAPI application and REST API
│   ├── load_testing.py       # Core load testing logic (Locust runner)
│   ├── locustfile.py         # CLI entry point
│   ├── models.py             # Tortoise-ORM database models
│   ├── loaders/
│   │   ├── config.py         # Pydantic settings
│   │   ├── database.py       # Database configuration
│   │   ├── logging.py        # Logging setup
│   │   └── app_lifespan.py   # FastAPI startup/shutdown lifecycle
│   └── templates/
│       └── index.html        # Web UI dashboard
├── reports/                  # Generated HTML and CSV reports
├── data/                     # Data storage
├── docs/                     # Additional documentation
├── example.env               # Example environment configuration
├── Pipfile                   # Python dependencies
└── README.md
```

## Configuration

Copy `example.env` to `.env` and adjust as needed:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_HOST` | `localhost` | Server host |
| `APP_PORT` | `8000` | Server port |
| `DATABASE_URL` | `sqlite:///load_testing.sqlite3` | Database connection string |
| `REPORTS_DIR` | `./reports` | Directory for generated reports |
| `LOG_LEVEL` | `DEBUG` | Logging level |

## Understanding the Report

### Summary Metrics
- **Total Requests** -- number of HTTP requests made during the test
- **Success Rate** -- percentage of successful requests (HTTP 200, 204)
- **Failed Requests** -- count of requests that returned errors
- **Avg Response Time** -- average response time across all requests

### Response Time Percentiles
- **Median (P50)** -- typical response time
- **P95** -- 95th percentile, covers most requests
- **P99** -- 99th percentile, worst-case (excluding outliers)

### Output Files

Each test generates files in the `reports/` directory:
- `locust_report_{test_id}.html` -- styled HTML report with metrics and charts
- `locust_results_{test_id}_stats.csv` -- detailed statistics for further analysis

## Test Parameter Guidelines

| Parameter | Light | Medium | Heavy | Stress |
|-----------|-------|--------|-------|--------|
| Users | 10-50 | 50-200 | 200-1000 | 1000+ |
| Duration | 30-60s | 120-300s | 300-600s | 600s+ |
| Ramp Rate | 1-2/s | 5-10/s | 20-50/s | 100+/s |

## Troubleshooting

- **Connection Refused** -- verify the target URL is correct and the service is running
- **Too Many Open Files** -- reduce users or run `ulimit -n 4096`
- **Test Already Running** -- the API allows one test at a time; wait for it to complete or check status at `/tests`

## References

- [Locust Documentation](https://docs.locust.io)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Tortoise-ORM Documentation](https://tortoise.github.io/)
