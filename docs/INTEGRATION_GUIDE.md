# Integration Guide - Using Load Testing Module

This guide shows how to use the modularized load testing code in different contexts.

## Architecture

```
┌─────────────────────────────────────────────────┐
│         load_testing.py (Core Module)           │
│  - run_load_test()                              │
│  - APIUser (Locust HttpUser)                    │
│  - create_html_report()                         │
│  - export_csv()                                 │
└─────────────────┬───────────────────────────────┘
                  │
        ┌─────────┴─────────┬─────────────┐
        │                   │             │
        v                   v             v
   ┌────────────┐   ┌──────────────┐   ┌──────────┐
   │ CLI Tool   │   │ Python Code  │   │ REST API │
   │ locustfile │   │ (import)     │   │ (api.py) │
   └────────────┘   └──────────────┘   └──────────┘
```

---

## 1. Command Line Interface (CLI)

### Basic Usage
```bash
pipenv shell
python locustfile.py -u http://example.com
```

### With Custom Parameters
```bash
python locustfile.py \
  --url https://api.example.com \
  --duration 60 \
  --users 50 \
  --ramp-rate 5 \
  --output my_test.html
```

### Short Options
```bash
python locustfile.py -u http://example.com -d 60 -n 50 -r 5 -o report.html
```

---

## 2. Python Code (Direct Import)

### Basic Test
```python
from load_testing import run_load_test

# Run a load test
results = run_load_test(url="http://example.com")

print(f"Requests: {results['total_requests']}")
print(f"Success Rate: {results['success_rate']:.2f}%")
print(f"Avg Response Time: {results['avg_response_time']:.2f}ms")
```

### Custom Parameters
```python
from load_testing import run_load_test

results = run_load_test(
    url="https://api.example.com/v1/users",
    duration=120,
    num_users=100,
    ramp_rate=10,
    html_report="custom_report.html",
    csv_prefix="custom_results"
)

# Access all results
print(results)
```

### With Progress Callback
```python
from load_testing import run_load_test

def on_progress(progress_data):
    """Called every 2 seconds with progress updates."""
    elapsed = progress_data['elapsed']
    users = progress_data['users']
    rps = progress_data['rps']
    print(f"{elapsed}s: {users} users, {rps:.2f} req/s")

results = run_load_test(
    url="http://example.com",
    duration=60,
    num_users=50,
    ramp_rate=5,
    verbose=False,  # Disable automatic printing
    progress_callback=on_progress
)
```

### In Your Application
```python
# my_app.py
from load_testing import run_load_test
import json

class PerformanceMonitor:
    def check_api_performance(self, api_url):
        """Check if API meets performance requirements."""

        results = run_load_test(
            url=api_url,
            duration=60,
            num_users=100,
            ramp_rate=10,
            verbose=False
        )

        # Check thresholds
        if results['avg_response_time'] > 500:
            return {"status": "warning", "message": "Slow response time"}

        if results['success_rate'] < 99:
            return {"status": "error", "message": "High failure rate"}

        return {"status": "ok", "message": "Performance acceptable"}

# Usage
monitor = PerformanceMonitor()
status = monitor.check_api_performance("http://api.example.com")
print(status)
```

---

## 3. REST API Endpoint

### Start Server
```bash
pipenv shell
python api.py
```

The API will be available at `http://localhost:8000`

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Start a Load Test
```bash
curl -X POST http://localhost:8000/load-test \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://example.com",
    "duration": 60,
    "num_users": 50,
    "ramp_rate": 5
  }'
```

**Response:**
```json
{
  "message": "Load test started",
  "test_id": "test_1234567890",
  "status": "pending",
  "url": "http://example.com",
  "duration": 60,
  "num_users": 50,
  "ramp_rate": 5
}
```

### Check Test Status
```bash
curl http://localhost:8000/load-test/test_1234567890
```

### Download Results
```bash
# Download HTML report
curl http://localhost:8000/load-test/test_1234567890/report > report.html

# Download CSV file
curl http://localhost:8000/load-test/test_1234567890/csv > results.csv
```

### List All Tests
```bash
curl http://localhost:8000/tests
```

### Example: Python Client for API
```python
import requests
import time

class LoadTestClient:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url

    def start_test(self, url, duration=120, num_users=100, ramp_rate=10):
        """Start a load test via API."""
        response = requests.post(
            f"{self.api_url}/load-test",
            json={
                "url": url,
                "duration": duration,
                "num_users": num_users,
                "ramp_rate": ramp_rate
            }
        )
        return response.json()

    def wait_for_results(self, test_id, timeout=3600):
        """Wait for test to complete and return results."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            response = requests.get(f"{self.api_url}/load-test/{test_id}")
            data = response.json()

            if data['status'] == 'completed':
                return data['results']
            elif data['status'] == 'failed':
                raise Exception(f"Test failed: {data.get('error')}")

            time.sleep(2)

        raise TimeoutError("Test did not complete in time")

# Usage
client = LoadTestClient()

# Start test
response = client.start_test("http://example.com", duration=60, num_users=50)
test_id = response['test_id']
print(f"Test started: {test_id}")

# Wait for results
try:
    results = client.wait_for_results(test_id)
    print(f"Success Rate: {results['success_rate']:.2f}%")
    print(f"Avg Response Time: {results['avg_response_time']:.2f}ms")
except TimeoutError:
    print("Test is taking longer than expected")
```

---

## 4. Docker Integration (Optional)

### Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install pipenv
RUN pip install pipenv

# Copy project files
COPY Pipfile Pipfile.lock ./
COPY load_testing.py locustfile.py api.py ./

# Install dependencies
RUN pipenv install --deploy --ignore-pipfile

# Expose API port
EXPOSE 8000

# Run API server
CMD ["pipenv", "run", "python", "api.py"]
```

### Run with Docker
```bash
# Build image
docker build -t load-tester .

# Run API server
docker run -p 8000:8000 load-tester

# Run CLI test
docker run load-tester pipenv run python locustfile.py -u http://example.com
```

---

## 5. Integration with CI/CD

### GitHub Actions Example
```yaml
name: Performance Tests

on: [push, pull_request]

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'

      - name: Install pipenv
        run: pip install pipenv

      - name: Install dependencies
        run: pipenv install

      - name: Run load test
        run: |
          pipenv run python locustfile.py \
            -u http://staging.example.com \
            -d 120 \
            -n 100 \
            -r 10 \
            -o test_results.html

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v2
        with:
          name: load-test-results
          path: test_results.html
```

### Jenkins Pipeline Example
```groovy
pipeline {
    agent any

    stages {
        stage('Setup') {
            steps {
                sh 'pipenv install'
            }
        }

        stage('Load Test') {
            steps {
                sh '''
                    pipenv run python locustfile.py \
                        -u http://staging.example.com \
                        -d 300 \
                        -n 200 \
                        -r 20 \
                        -o jenkins_report.html
                '''
            }
        }

        stage('Analyze Results') {
            steps {
                script {
                    // Parse results and fail if needed
                    sh 'python analyze_results.py'
                }
            }
        }
    }

    post {
        always {
            publishHTML([
                reportDir: '.',
                reportFiles: 'jenkins_report.html',
                reportName: 'Load Test Report'
            ])
        }
    }
}
```

---

## 6. Advanced Usage Examples

### Example: Scheduled Monitoring
```python
# monitor.py
import schedule
import time
from load_testing import run_load_test
from datetime import datetime

def daily_health_check():
    """Run daily health check."""
    print(f"[{datetime.now()}] Running health check...")

    results = run_load_test(
        url="https://api.example.com",
        duration=60,
        num_users=100,
        ramp_rate=10,
        verbose=False,
        csv_prefix="daily_check"
    )

    # Alert if performance degrades
    if results['avg_response_time'] > 500:
        send_alert(f"API response time: {results['avg_response_time']:.2f}ms")

    if results['success_rate'] < 99:
        send_alert(f"API failure rate: {100 - results['success_rate']:.2f}%")

def send_alert(message):
    """Send alert (Slack, Email, etc.)."""
    # Implementation here
    pass

# Schedule
schedule.every().day.at("09:00").do(daily_health_check)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Example: Capacity Planning
```python
# capacity_planner.py
from load_testing import run_load_test

def find_max_capacity(api_url, min_success_rate=0.95):
    """Find maximum capacity before degradation."""

    load_levels = [50, 100, 200, 500, 1000]

    for load in load_levels:
        print(f"\nTesting at {load} users...")

        results = run_load_test(
            url=api_url,
            duration=60,
            num_users=load,
            ramp_rate=load / 10,
            verbose=False,
            csv_prefix=f"capacity_{load}"
        )

        print(f"Success Rate: {results['success_rate']:.2f}%")
        print(f"Avg Response: {results['avg_response_time']:.2f}ms")

        if results['success_rate'] < min_success_rate:
            return load - 50  # Return previous level

    return load_levels[-1]

# Usage
max_capacity = find_max_capacity("http://api.example.com")
print(f"\nMax capacity: {max_capacity} concurrent users")
```

---

## Return Value Structure

The `run_load_test()` function returns a dictionary with:

```python
{
    'total_requests': 5000,           # Total HTTP requests made
    'total_failures': 50,              # Number of failed requests
    'success_rate': 99.0,              # Percentage of successful requests
    'avg_response_time': 145.32,       # Average response time in ms
    'median_response_time': 120.5,     # Median (P50) response time
    'p95_response_time': 350.2,        # 95th percentile response time
    'p99_response_time': 450.8,        # 99th percentile response time
    'csv_file': 'locust_results_stats.csv',  # Path to CSV file
    'html_report': 'locust_report.html',     # Path to HTML report
    'url': 'http://example.com',       # Target URL
    'duration': 120,                   # Test duration in seconds
    'num_users': 100,                  # Number of concurrent users
    'ramp_rate': 10                    # Ramp-up rate (users/second)
}
```

---

## Summary

| Method | Best For | Example |
|--------|----------|---------|
| **CLI** | Quick tests, scripting | `python locustfile.py -u http://example.com` |
| **Import** | Application integration, complex logic | `from load_testing import run_load_test` |
| **REST API** | Remote testing, UI dashboards | `curl -X POST http://localhost:8000/load-test` |
| **Docker** | Containerized deployment | `docker run load-tester` |
| **CI/CD** | Automated performance testing | GitHub Actions, Jenkins, GitLab CI |

Choose the method that best fits your workflow!
