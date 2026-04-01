# Modularized Load Testing - File Structure

## 📁 Project Structure

```
load-tester/
├── load_testing.py          ⭐ Core module (reusable library)
├── locustfile.py            CLI entry point (uses load_testing.py)
├── api.py                   FastAPI REST endpoint (uses load_testing.py)
├── examples.py              Usage examples
├── INTEGRATION_GUIDE.md      Integration documentation
├── README.md                Original documentation
├── QUICKSTART.md            Quick start guide
├── EXAMPLES.md              Scenario examples
└── run_test.sh              Helper shell script
```

---

## 🎯 Core Components

### 1. **load_testing.py** (Core Library)
The heart of the system. Contains all load testing logic.

**Key Functions:**
- `run_load_test()` - Main function to run load tests
- `export_csv()` - Export statistics to CSV
- `create_html_report()` - Generate HTML reports

**Key Classes:**
- `APIUser` - Locust HttpUser for making requests

**Features:**
- ✅ Reusable in any Python code
- ✅ Optional progress callbacks
- ✅ Verbose/silent mode
- ✅ Returns detailed results dictionary
- ✅ Generates CSV and HTML reports

**Import and Use:**
```python
from load_testing import run_load_test

results = run_load_test(url="http://example.com")
```

---

### 2. **locustfile.py** (CLI Tool)
Command-line interface wrapper around `load_testing.py`.

**Features:**
- ✅ Command-line argument parsing
- ✅ Default values (duration=120s, users=100, ramp-rate=10)
- ✅ Pretty printed progress and results

**Usage:**
```bash
python locustfile.py -u http://example.com
python locustfile.py -u http://example.com -d 60 -n 50 -r 5
```

---

### 3. **api.py** (REST API Server)
FastAPI server to trigger and monitor load tests via HTTP.

**Endpoints:**
- `POST /load-test` - Start a new load test
- `GET /load-test/{test_id}` - Get test results
- `GET /load-test/{test_id}/report` - Download HTML report
- `GET /load-test/{test_id}/csv` - Download CSV file
- `GET /tests` - List all tests
- `GET /docs` - Swagger API documentation

**Usage:**
```bash
python api.py  # Starts server on http://localhost:8000

# Then in another terminal:
curl -X POST http://localhost:8000/load-test \
  -H "Content-Type: application/json" \
  -d '{"url": "http://example.com", "duration": 60, "num_users": 50}'
```

---

### 4. **examples.py** (Usage Examples)
Contains 6 practical examples showing different use cases.

**Examples:**
1. `example_1_basic_test()` - Basic test with defaults
2. `example_2_custom_parameters()` - Custom test parameters
3. `example_3_with_progress_callback()` - Progress monitoring
4. `example_4_stress_test()` - Progressive load testing
5. `example_5_before_after_comparison()` - Performance comparison
6. `example_6_multiple_endpoints()` - Test multiple APIs

**Run Examples:**
```bash
# Edit examples.py and uncomment what you want to run
python examples.py
```

---

## 🔄 How They Work Together

```
User/Application
    │
    ├─────────────────┬─────────────────┬─────────────┐
    │                 │                 │             │
    v                 v                 v             v
  CLI             Python Code         REST API      Monitoring
  (locustfile)    (import)            (api.py)      (examples)
    │                 │                 │             │
    └─────────────────┴─────────────────┴─────────────┘
                      │
                      v
              load_testing.py
              (Core Library)
                      │
         ┌────────────┼────────────┐
         │            │            │
         v            v            v
     APIUser      HTML Report    CSV Export
   (Locust)       (Beautiful)    (Data)
```

---

## 📋 Use Cases

### Scenario 1: Quick CLI Test
```bash
pipenv shell
python locustfile.py -u http://myapp.com
```
✅ Simple, direct, no coding needed

---

### Scenario 2: Automated Performance Testing in Python
```python
from load_testing import run_load_test

results = run_load_test(url="http://myapp.com")
assert results['success_rate'] > 99
```
✅ Integrate into your application

---

### Scenario 3: Remote Testing via API
```bash
# Server 1: Start API
python api.py

# Server 2: Trigger test
curl -X POST http://server1:8000/load-test \
  -H "Content-Type: application/json" \
  -d '{"url": "http://myapp.com"}'
```
✅ Distributed testing setup

---

### Scenario 4: CI/CD Pipeline
```yaml
- run: pipenv run python locustfile.py -u http://staging.example.com
- if: failure()
  run: echo "Performance test failed!"
```
✅ Automated performance checks

---

## 🎛️ Configuration

### Default Values (in locustfile.py)
```python
--duration 120      # Test duration in seconds
--users 100         # Concurrent users
--ramp-rate 10      # Users spawned per second
```

### To Change Defaults
Edit [locustfile.py](locustfile.py) line ~30:
```python
parser.add_argument('--duration', '-d', type=int, default=120)  # Change here
parser.add_argument('--users', '-n', type=int, default=100)     # Change here
parser.add_argument('--ramp-rate', '-r', type=float, default=10)  # Change here
```

---

## 📊 Output Files

After running a test, you get:
- `locust_report.html` - Beautiful interactive HTML report
- `locust_results_stats.csv` - Detailed statistics in CSV format

---

## 🚀 Getting Started

### 1. Via CLI (Easiest)
```bash
pipenv shell
python locustfile.py -u http://example.com
```

### 2. Via Python Code
```python
from load_testing import run_load_test
results = run_load_test(url="http://example.com")
```

### 3. Via REST API
```bash
python api.py  # Start server
# Then use curl or any HTTP client
```

### 4. See Examples
```bash
python examples.py
```

---

## 📚 Documentation

- **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** - How to use in different contexts
- **[README.md](README.md)** - Features and overview
- **[QUICKSTART.md](QUICKSTART.md)** - Quick reference
- **[EXAMPLES.md](EXAMPLES.md)** - Real-world scenarios

---

## 🔗 Function Signatures

### `run_load_test()`
```python
def run_load_test(
    url,                          # Required: target URL
    duration=120,                 # Test duration in seconds
    num_users=100,                # Concurrent users
    ramp_rate=10,                 # Users per second
    csv_prefix=None,              # CSV filename prefix
    html_report=None,             # HTML report filename
    verbose=True,                 # Print progress
    progress_callback=None        # Custom progress handler
) -> dict:
    """Returns dictionary with results"""
```

---

## 💡 Pro Tips

1. **For Quick Tests:** Use CLI with defaults
2. **For Integration:** Import `run_load_test` directly
3. **For Remote Testing:** Use the REST API
4. **For Monitoring:** Set up API server and poll results
5. **For CI/CD:** Use CLI in pipeline scripts

---

## 🎯 Architecture Benefits

| Aspect | Benefit |
|--------|---------|
| **Modularity** | Core logic in one place, multiple interfaces |
| **Reusability** | Use same code from CLI, Python, API |
| **Flexibility** | Easy to extend for custom needs |
| **Maintainability** | Changes in one module benefit all interfaces |
| **Testability** | Can test core logic independently |
| **Scalability** | Ready for docker, cloud, distributed setups |

---

## 🔧 Extending the Module

### Add Custom Request Types
Edit `load_testing.py` APIUser class:
```python
@task
def post_request(self):
    """Add POST requests."""
    with self.client.post(self.target_path, json={"key": "value"}) as response:
        # Handle response
        pass
```

### Add Custom Metrics
Modify `create_html_report()` or `export_csv()` functions.

### Add Authentication
Extend APIUser with auth headers:
```python
@property
def auth_headers(self):
    return {"Authorization": "Bearer token"}
```

---

## 📞 Quick Reference

| Task | Command/Code |
|------|--------------|
| Quick test | `python locustfile.py -u http://example.com` |
| Custom params | `python locustfile.py -u http://example.com -d 60 -n 50 -r 5` |
| Import module | `from load_testing import run_load_test` |
| Start API | `python api.py` |
| See examples | `python examples.py` |
| View API docs | `http://localhost:8000/docs` |

---

## ✅ Validation Checklist

- [x] Core module separated (`load_testing.py`)
- [x] CLI wrapper created (`locustfile.py`)
- [x] REST API implemented (`api.py`)
- [x] Examples provided (`examples.py`)
- [x] Documentation complete (`INTEGRATION_GUIDE.md`)
- [x] All interfaces working
- [x] Results available in multiple formats (HTML, CSV)

---

**Ready to use! Choose your integration method and get started! 🚀**
