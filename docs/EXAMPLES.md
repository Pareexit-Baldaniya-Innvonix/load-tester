# Load Testing Examples

This document provides practical examples for different load testing scenarios.

## Table of Contents
1. [Basic API Testing](#basic-api-testing)
2. [Website Load Testing](#website-load-testing)
3. [Stress Testing](#stress-testing)
4. [Endurance Testing](#endurance-testing)
5. [Capacity Planning](#capacity-planning)

---

## Basic API Testing

### Test a REST API endpoint
```bash
# Activate pipenv shell first
pipenv shell

# Test a single endpoint for 60 seconds with 50 users
python locustfile.py -u https://api.example.com/v1/users -d 60 -n 50 -r 5
```

**What this does:**
- ✅ Makes GET and HEAD requests to the API endpoint
- ✅ Gradually ramps up from 0 to 50 users over 10 seconds (50 users ÷ 5 per second)
- ✅ Continues testing for 60 seconds total
- ✅ Generates `locust_report.html` with detailed results

**Best for:**
- Validating API performance
- Finding baseline response times
- Identifying bottlenecks before heavy load

---

## Website Load Testing

### Test a live website
```bash
pipenv shell

# 2-minute test with 100 concurrent users
./run_test.sh https://www.example.com 120 100 10 website_test.html
```

**What this does:**
- ✅ Simulates 100 real users accessing the website simultaneously
- ✅ Users ramp up gradually: 1 user every 0.1 seconds
- ✅ Runs for 2 minutes (gives time for caching to warm up)
- ✅ Saves results to `website_test.html`

**Expected Results:**
- Response times: 200-500ms (typical for web pages)
- Success rate: 95%+ (some users may see slow responses)
- Peak requests/sec: ~50-100

---

## Stress Testing

### Push a service to its limits
```bash
pipenv shell

# 5-minute stress test: ramp to 500 users
python locustfile.py \
  --url http://localhost:8000 \
  --duration 300 \
  --users 500 \
  --ramp-rate 20 \
  --output stress_test_final.html
```

**Timeline:**
- 0-25s: Ramp-up (500 users ÷ 20 per second = 25 seconds)
- 25-300s: Sustained load testing (275 seconds at full capacity)

**Look for:**
- ❌ When does the service start failing?
- ⚠️ Do response times increase significantly?
- 📊 What's the breaking point?

### Spike Test (sudden traffic surge)
```bash
pipenv shell

# Quick ramp-up simulating unexpected traffic spike
python locustfile.py \
  --url http://localhost:8000 \
  --duration 120 \
  --users 200 \
  --ramp-rate 50 \
  --output spike_test.html
```

**What happens:**
- All 200 users spawn in just 4 seconds
- Simulates sudden traffic spike
- Reveals issues with request queueing and timeouts

---

## Endurance Testing

### Long-running stability test
```bash
pipenv shell

# 30-minute test at moderate load
python locustfile.py \
  --url https://api.example.com \
  --duration 1800 \
  --users 100 \
  --ramp-rate 2 \
  --output endurance_test.html
```

**What this tests:**
- ✅ Memory leaks (gradual performance degradation?)
- ✅ Connection pool exhaustion
- ✅ Database connection limits
- ✅ Cache eviction behavior

**Success indicators:**
- Response times remain stable throughout
- No increase in failure rate over time
- Tail latencies (P99) don't increase

---

## Capacity Planning

### Three-tier load testing
Find your service's capacity limits:

```bash
pipenv shell

# Test 1: Light load
echo "Phase 1: Light Load Test"
python locustfile.py -u http://api.example.com -d 120 -n 50 -r 5 -o capacity_light.html

# Test 2: Medium load
echo "Phase 2: Medium Load Test"
python locustfile.py -u http://api.example.com -d 120 -n 200 -r 10 -o capacity_medium.html

# Test 3: Heavy load
echo "Phase 3: Heavy Load Test"
python locustfile.py -u http://api.example.com -d 120 -n 500 -r 20 -o capacity_heavy.html
```

**Analyze results:**
1. Compare response times across all three tests
2. Find where response time degrades significantly
3. Identify your service's "comfort zone"
4. Plan infrastructure accordingly

### Example Results Table:

| Load Level | Users | Avg Response | P95 Response | Success Rate |
|-----------|-------|--------------|--------------|--------------|
| Light     | 50    | 45ms         | 65ms         | 99.9%        |
| Medium    | 200   | 120ms        | 250ms        | 99.5%        |
| Heavy     | 500   | 850ms        | 2000ms       | 95%          |

💡 **Insight**: Response time acceptable up to 200 users. Degrade at 500. Recommend provisioning for 300 users with 20% headroom.

---

## Real-World Scenarios

### Scenario: E-commerce Site Pre-Sale
Before a big sale event, verify your infrastructure can handle the expected traffic:

```bash
pipenv shell

# Expected: 2x normal traffic during sale
# Normal: 100 concurrent users
# Expected: 200 concurrent users for 1 hour

python locustfile.py \
  --url https://shop.example.com \
  --duration 3600 \
  --users 200 \
  --ramp-rate 10 \
  --output presale_check.html
```

### Scenario: New Feature Rollout
Test new endpoints before production release:

```bash
pipenv shell

# Test new payment API endpoint
python locustfile.py \
  --url https://api.example.com/v2/payments \
  --duration 300 \
  --users 100 \
  --ramp-rate 5 \
  --output payment_api_test.html
```

### Scenario: Database Migration
Verify performance before and after migration:

```bash
pipenv shell

# Before migration
echo "Testing OLD database"
python locustfile.py -u http://app.example.com -d 120 -n 50 -r 5 -o before_migration.html

# After migration (run migration scripts)
sleep 30  # Give time for stabilization

# After migration
echo "Testing NEW database"
python locustfile.py -u http://app.example.com -d 120 -n 50 -r 5 -o after_migration.html
```

Then compare `before_migration.html` vs `after_migration.html`

---

## Interpreting Results

### Key Metrics to Watch

**Response Time (Latency)**
- `< 100ms`: Excellent (most users won't perceive lag)
- `100-300ms`: Good (acceptable for most apps)
- `300-1000ms`: Fair (noticeable to users)
- `> 1000ms`: Poor (frustrating user experience)

**Success Rate**
- `> 99%`: Excellent (very reliable)
- `95-99%`: Good (occasional failures)
- `< 95%`: Bad (frequent failures)

**Requests/Second**
- Calculated from: `Total Requests ÷ Duration`
- Shows throughput capacity

**Error Analysis**
- Connection errors: Network/infrastructure issues
- Timeouts: Service too slow
- 5xx errors: Application errors

---

## Tips & Best Practices

✅ **DO**
- Start with small loads and increase gradually
- Run tests during quiet hours to avoid impacting users
- Test realistic request patterns (not just GET)
- Include think time between requests
- Rerun tests multiple times for consistency
- Monitor target service during tests
- Document baseline measurements

❌ **DON'T**
- Test production without permission
- Assume one test is enough (run multiple times)
- Test with more users than you expect to handle
- Ignore CPU/memory metrics on target service
- Forget to analyze results thoroughly

---

## Troubleshooting Test Results

**Problem: High failure rate**
- ❌ Service may be overloaded
- ❌ Network connectivity issues
- ❌ Incorrect URL or endpoint
- ✅ Solution: Reduce user count, check URL, monitor service logs

**Problem: All users fail immediately**
```bash
# Check connectivity first
curl -I https://api.example.com/v1/users

# Try with fewer users
python locustfile.py -u https://api.example.com/v1/users -d 30 -n 5 -r 1
```

**Problem: Response times increase dramatically mid-test**
- ❌ Service running out of resources
- ❌ Database connections exhausted
- ❌ Memory leak in application
- ✅ Check service metrics during test

**Problem: Inconsistent results between runs**
- Try running tests at different times
- Check if service has auto-scaling enabled
- Ensure no background jobs running on service

---

## Next Steps

1. **Run your first test:**
   ```bash
   pipenv shell
   ./run_test.sh http://your-api.com 60 50 5
   ```

2. **Review the HTML report** - Open in your browser

3. **Analyze results:**
   - What's the baseline response time?
   - Any errors occurring?
   - Is success rate acceptable?

4. **Iterate:**
   - Try different user counts
   - Test different endpoints
   - Benchmark before/after changes

For more information, see [README.md](README.md)
