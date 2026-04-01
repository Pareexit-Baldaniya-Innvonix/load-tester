# Quick Start Guide

## 30-Second Setup

### 1. Activate Pipenv
```bash
cd load-tester
pipenv shell
```

### 2. Run Your First Test
```bash
# Simplest - uses defaults (120s duration, 100 users, 10 ramp-rate)
python locustfile.py -u http://example.com

# Or customize it
python locustfile.py -u http://example.com -d 60 -n 50 -r 5
```

### 3. View Results
Open `locust_report.html` in your browser 🎉

---

## Common Commands

### Using Python directly
```bash
pipenv shell

# Minimal - uses all defaults (120s, 100 users, 10 ramp-rate)
python locustfile.py -u URL

# Full control
python locustfile.py -u URL -d DURATION -n USERS -r RAMP_RATE

# Example:
python locustfile.py -u https://api.example.com
python locustfile.py -u https://api.example.com -d 120 -n 100 -r 10
```

### Using the helper script
```bash
./run_test.sh URL DURATION USERS RAMP_RATE [OUTPUT_FILE]

# Example:
./run_test.sh https://api.example.com 120 100 10 test_report.html
```

---

## Quick Parameter Reference

### Light Test (validation)
```bash
python locustfile.py -u $URL -d 60 -n 20 -r 2
```
- 1 minute duration
- 20 users
- Slow ramp-up (1 user every 0.5s)

### Standard Test (baseline)
```bash
python locustfile.py -u $URL -d 120 -n 50 -r 5
```
- 2 minutes duration
- 50 users
- Normal ramp-up (1 user every 0.2s)

### Heavy Test (stress)
```bash
python locustfile.py -u $URL -d 300 -n 200 -r 20
```
- 5 minutes duration
- 200 users
- Fast ramp-up (1 user every 0.05s)

### Spike Test (sudden load)
```bash
python locustfile.py -u $URL -d 120 -n 500 -r 100
```
- 2 minutes duration
- 500 users
- Very fast ramp-up (all in 5 seconds)

### Endurance Test (stability)
```bash
python locustfile.py -u $URL -d 1800 -n 100 -r 2
```
- 30 minutes duration
- 100 users
- Very slow ramp-up (1 user every 0.5s)

---

## Parameter Cheat Sheet

| Parameter | Range | Default | Example |
|-----------|-------|---------|---------|
| Duration | 30-3600 seconds | Required | `-d 120` |
| Users | 1-10000+ | Required | `-n 100` |
| Ramp-rate | 0.1-100 users/sec | Required | `-r 5` |
| Output file | Any filename | `locust_report.html` | `-o test.html` |

### Calculating Ramp-up Time
- **Formula**: Users ÷ Ramp-rate = seconds
- **Example**: 100 users ÷ 5 per second = 20 seconds to reach full load
- **Keep ramp-up time 10-30% of total duration**

---

## Output Files

After running a test:
- `locust_report.html` - **Beautiful HTML report** (open in browser)
- `locust_results_stats.csv` - Detailed CSV data

### Report Contents
✅ Test parameters
✅ Summary metrics (requests, failures, response times)
✅ Response time percentiles (P50, P95, P99)
✅ Per-endpoint statistics

---

## Troubleshooting

### Connection Issues
```bash
# Test URL is accessible
curl -I http://example.com

# Try with simpler URL
./run_test.sh http://localhost:8000 30 10 2
```

### Permission Denied
```bash
# Make script executable
chmod +x run_test.sh
```

### Pipenv Not Found
```bash
# Check pipenv is installed
which pipenv

# Install if needed
pip install pipenv

# Activate the environment
pipenv shell
```

### Too Many Users
```bash
# If getting "too many open files" error:
ulimit -n 4096

# Then retry with fewer users
python locustfile.py -u $URL -d 60 -n 100 -r 5
```

---

## Real-World Examples

```bash
# Test API endpoint (quick check)
python locustfile.py -u https://api.myapp.com/v1/users -d 60 -n 50 -r 5

# Test website before launch
./run_test.sh https://myapp.com 300 200 10 presale_test.html

# Stress test at 3x normal load
python locustfile.py -u http://api.myapp.com -d 300 -n 300 -r 20 -o stress_3x.html

# Run 30-minute endurance test
python locustfile.py -u http://localhost:8000 -d 1800 -n 50 -r 1 -o endurance.html

# Quick spike test (sudden 1000 users)
python locustfile.py -u http://api.myapp.com -d 120 -n 1000 -r 200 -o spike.html
```

---

## Interpreting the HTML Report

### "Success Rate: 98%"
- ✅ 98% of requests returned successfully
- ❌ 2% failed (connections, timeouts, errors)

### "Avg Response Time: 150ms"
- Average time to complete a request
- Under 100ms is excellent, over 1000ms is poor

### "P95 Response Time: 350ms"
- 95% of requests completed in 350ms or less
- 5% took longer (slower requests)

### "Total Requests: 5000"
- 5000 HTTP requests made during the entire test
- Higher = more throughput tested

---

## More Info

- [Full README](README.md) - Detailed documentation
- [Examples](EXAMPLES.md) - Real-world scenarios
- [Locust Docs](https://docs.locust.io) - Advanced features

---

**Pro Tips:**
- 💾 Save reports with descriptive names: `test_before_optimization.html`
- 📊 Compare before/after tests to measure improvements
- 🔄 Run same test 2-3 times for consistency
- 📈 Gradually increase load to find your limits
- 🎯 Focus on P95 and P99, not just average response time

**Happy Load Testing! 🚀**
