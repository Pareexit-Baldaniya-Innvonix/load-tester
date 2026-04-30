import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import asyncio
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from typing import Optional

import aiofiles
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

# Local imports
from .loaders.app_lifespan import app_lifespan
from .models import LoadTest, TestMetrics

app = FastAPI(title="Load Testing API", version="1.0.0", lifespan=app_lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the templates directory
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"

# In-memory store for test results
test_results = {}
current_test = None

# Tracks the Future for each running test so we can cancel it
running_futures: dict = {}

process_pool = ProcessPoolExecutor(max_workers=4)

# cleanliness
@app.on_event("startup")
async def cleanup_stale_running_tests():
    """
    On every server startup, any test that is still marked 'running' in the DB
    was interrupted by a crash or restart and will never complete.
    Mark them all as 'failed' so the database stays consistent.
    """
    try:
        stale = await LoadTest.filter(status="running").all()
        for test in stale:
            test.status = "failed"
            test.error_message = "Server restarted while test was running"
            test.completed_at = datetime.utcnow()
            await test.save()
        if stale:
            pass
    except Exception:
        pass


class LoadTestRequest(BaseModel):
    """Request model for load testing."""

    url: str
    duration: int = 60
    num_users: int = 100
    ramp_rate: float = 10
    csv_prefix: str = "locust_results"
    html_report: str = "locust_report.html"


class LoadTestResponse(BaseModel):
    """Response model for load test results."""

    message: str
    test_id: Optional[str] = None
    status: str
    url: str
    duration: int
    num_users: int
    ramp_rate: float
    results: Optional[dict] = None


def run_load_test_in_process(
    url: str,
    duration: int,
    num_users: int,
    ramp_rate: float,
    csv_prefix: str,
    html_report: str,
) -> dict:
    """
    Executed inside a worker process.  Imports are done here so that the
    heavy Locust machinery is only loaded in the child, not in the main
    FastAPI process.
    """

    from .load_testing import run_load_test

    return run_load_test(
        url=url,
        duration=duration,
        num_users=num_users,
        ramp_rate=ramp_rate,
        csv_prefix=csv_prefix,
        html_report=html_report,
        verbose=False,
    )


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web UI dashboard."""
    html_file = TEMPLATES_DIR / "index.html"
    if html_file.exists():
        async with aiofiles.open(html_file, mode="r") as f:
            return await f.read()
    return "<h1>Load Testing Dashboard</h1><p>UI file not found</p>"


@app.get("/api", response_class=JSONResponse)
async def api_info():
    """API information endpoint."""
    return {
        "name": "Load Testing API",
        "version": "1.0.0",
        "endpoints": {
            "POST /load-test": "Start a new load test",
            "GET /load-test/{test_id}": "Get results of a specific test",
            "GET /load-test/{test_id}/report": "Download HTML report",
            "GET /load-test/{test_id}/csv": "Download CSV file",
            "GET /tests": "List all tests",
        },
    }


@app.post("/load-test", response_model=LoadTestResponse)
async def start_load_test(request: LoadTestRequest, background_tasks: BackgroundTasks):
    """
    Start a new load test.

    Parameters:
    - url: Target URL to test
    - duration: Test duration in seconds (default: 120)
    - num_users: Maximum concurrent users (default: 100)
    - ramp_rate: Users spawned per second (default: 10)
    - csv_prefix: Prefix for CSV files (default: locust_results)
    - html_report: HTML report filename (default: locust_report.html)

    Returns:
    - message: Status message
    - test_id: ID to track the test
    - status: Current status (pending/running/completed)
    """

    global current_test

    test_id = f"test_{int(asyncio.get_event_loop().time())}"
    current_test = test_id

    # Store initial test info
    test_results[test_id] = {
        "status": "running",
        "request": request.dict(),
        "results": None,
        "started_at": datetime.utcnow().isoformat() + "Z",
    }

    # Run test in background
    async def run_test():
        global current_test
        db_test = None

        reports_dir = os.getenv("REPORTS_DIR", "./reports")
        unique_html_report = f"locust_report_{test_id}.html"
        unique_csv_prefix = f"locust_results_{test_id}"

        try:
            # Create database record
            db_test = await LoadTest.create(
                test_id=test_id,
                url=request.url,
                duration=request.duration,
                num_users=request.num_users,
                ramp_rate=request.ramp_rate,
                status="running",
                started_at=datetime.utcnow(),
            )

            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(
                process_pool,
                run_load_test_in_process,
                request.url,
                request.duration,
                request.num_users,
                request.ramp_rate,
                unique_csv_prefix,
                unique_html_report,
            )
            running_futures[test_id] = future
            results: dict = await future

            html_path = str(Path(reports_dir) / unique_html_report)
            csv_path = str(Path(reports_dir) / f"{unique_csv_prefix}_stats.csv")

            # Update in-memory store
            test_results[test_id].update(
                {
                    "status": "completed",
                    "results": results,
                    "html_file": html_path,
                    "csv_file": csv_path,
                }
            )

            # Persist results to DB
            db_test.status = "completed"
            db_test.total_requests = int(results["total_requests"])
            db_test.total_failures = int(results["total_failures"])
            db_test.success_rate = float(results["success_rate"])
            db_test.avg_response_time = float(results["avg_response_time"])
            db_test.median_response_time = float(results["median_response_time"])
            db_test.p95_response_time = float(results["p95_response_time"])
            db_test.p99_response_time = float(results["p99_response_time"])
            db_test.html_report = html_path
            db_test.csv_file = csv_path
            db_test.completed_at = datetime.utcnow()
            await db_test.save()

        except Exception as e:
            test_results[test_id]["status"] = "failed"
            test_results[test_id]["error"] = str(e)

            # Update database with error
            if db_test:
                db_test.status = "failed"
                db_test.error_message = str(e)
                db_test.completed_at = datetime.utcnow()
                await db_test.save()
            else:
                # Create failed record if initial creation failed
                try:
                    await LoadTest.create(
                        test_id=test_id,
                        url=request.url,
                        duration=request.duration,
                        num_users=request.num_users,
                        ramp_rate=request.ramp_rate,
                        status="failed",
                        error_message=str(e),
                        created_at=datetime.utcnow(),
                    )
                except Exception:
                    pass  # Silently ignore DB errors at this stage

        finally:
            running_futures.pop(test_id, None)
            current_test = None

    background_tasks.add_task(run_test)

    return LoadTestResponse(
        message="Load test started",
        test_id=test_id,
        status="pending",
        url=request.url,
        duration=request.duration,
        num_users=request.num_users,
        ramp_rate=request.ramp_rate,
    )


@app.get("/load-test/{test_id}")
async def get_test_results(test_id: str):
    """Get results of a specific test."""

    if test_id not in test_results:
        raise HTTPException(status_code=404, detail="Test not found")

    test = test_results[test_id]

    if test["status"] == "running":
        return {
            "message": "Test is still running",
            "test_id": test_id,
            "status": "running",
        }

    if test["status"] == "failed":
        return {
            "message": "Test failed",
            "test_id": test_id,
            "status": "failed",
            "error": test.get("error"),
        }

    return {
        "message": "Test completed",
        "test_id": test_id,
        "status": "completed",
        "request": test["request"],
        "results": test["results"],
    }


@app.get("/load-test/{test_id}/report")
async def download_report(test_id: str):
    """Download HTML report for a test."""

    file_path = f"reports/locust_report_{test_id}.html"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(
        path=file_path,
        filename=f"report_{test_id}.html",
        media_type="text/html",
        headers={
            "Content-Length": str(os.path.getsize(file_path))
        },  # Added for progress tracking
    )


@app.get("/load-test/{test_id}/csv")
async def download_csv(test_id: str):
    """Download CSV report for a test."""

    if test_id not in test_results:
        raise HTTPException(status_code=404, detail="Test not found")

    test = test_results[test_id]

    if test["status"] != "completed":
        raise HTTPException(status_code=400, detail="Test not completed yet")

    # Use the exact path written by run_load_test
    csv_file = test.get("csv_file", f"locust_results_{test_id}_stats.csv")
    if not Path(csv_file).exists():
        raise HTTPException(
            status_code=404, detail=f"CSV file not found on disk: {csv_file}"
        )
    filename_only = Path(csv_file).name
    return FileResponse(
        csv_file,
        media_type="text/csv",
        filename=filename_only,
        headers={"Content-Disposition": f'attachment; filename="{filename_only}"'},
    )


@app.delete("/load-test/{test_id}/stop")
async def stop_load_test(test_id: str):
    """Cancel a running load test."""
    if test_id not in test_results:
        raise HTTPException(status_code=404, detail="Test not found")

    if test_results[test_id]["status"] != "running":
        return {"message": f"Test {test_id} is not running", "test_id": test_id}

    # Cancel the future — this works for executor futures in Python 3.9+
    future = running_futures.get(test_id)
    if future:
        future.cancel()
        running_futures.pop(test_id, None)

    # Mark as stopped in memory immediately
    test_results[test_id]["status"] = "failed"
    test_results[test_id]["error"] = "Stopped by user"

    global current_test
    if current_test == test_id:
        current_test = None

    # Also update the database record so it doesn't stay stuck as "running"
    try:
        db_test = await LoadTest.get(test_id=test_id)
        db_test.status = "failed"
        db_test.error_message = "Stopped by user"
        db_test.completed_at = datetime.utcnow()
        await db_test.save()
    except Exception:
        pass  # Silently ignore if the DB record doesn't exist yet

    return {"message": f"Test {test_id} stopped", "test_id": test_id}


@app.get("/tests")
async def list_tests():
    """List all tests and their status."""
    
    return {
        "tests": [
            {
                "test_id": test_id,
                "status": test["status"],
                "url": test["request"]["url"],
                "duration": test["request"].get("duration"),
                "num_users": test["request"].get("num_users"),
                "ramp_rate": test["request"].get("ramp_rate"),
                "results": test.get("results"),
                "error": test.get("error"),
                "started_at": test.get("started_at"),
            }
            for test_id, test in test_results.items()
        ],
        "total": len(test_results),
        "current_test": current_test,
    }


# Database endpoints
@app.get("/db/tests")
async def get_all_tests_from_db(limit: int = 50, offset: int = 0):
    """Get all tests from database with pagination."""
    tests = await LoadTest.all().offset(offset).limit(limit).order_by("-created_at")

    return {
        "tests": [
            {
                "test_id": test.test_id,
                "url": test.url,
                "status": test.status,
                "duration": test.duration,
                "num_users": test.num_users,
                "ramp_rate": test.ramp_rate,
                "success_rate": test.success_rate,
                "avg_response_time": test.avg_response_time,
                "total_requests": test.total_requests,
                "total_failures": test.total_failures,
                "created_at": test.created_at.isoformat(),
                "completed_at": (
                    test.completed_at.isoformat() if test.completed_at else None
                ),
            }
            for test in tests
        ],
        "total": await LoadTest.all().count(),
    }


@app.get("/db/tests/{test_id}")
async def get_test_from_db(test_id: str):
    """Get a specific test from database."""
    try:
        test = await LoadTest.get(test_id=test_id)

        return {
            "test_id": test.test_id,
            "url": test.url,
            "status": test.status,
            "duration": test.duration,
            "num_users": test.num_users,
            "ramp_rate": test.ramp_rate,
            "total_requests": test.total_requests,
            "total_failures": test.total_failures,
            "success_rate": test.success_rate,
            "avg_response_time": test.avg_response_time,
            "median_response_time": test.median_response_time,
            "p95_response_time": test.p95_response_time,
            "p99_response_time": test.p99_response_time,
            "html_report": test.html_report,
            "csv_file": test.csv_file,
            "error_message": test.error_message,
            "created_at": test.created_at.isoformat(),
            "started_at": test.started_at.isoformat() if test.started_at else None,
            "completed_at": (
                test.completed_at.isoformat() if test.completed_at else None
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Test not found: {str(e)}")


@app.get("/db/stats")
async def get_database_stats():
    """Get statistics about all tests in database."""
    total_tests = await LoadTest.all().count()
    completed_tests = await LoadTest.filter(status="completed").count()
    failed_tests = await LoadTest.filter(status="failed").count()
    running_tests = await LoadTest.filter(status="running").count()

    # Get average metrics from completed tests
    completed = await LoadTest.filter(status="completed").all()

    if completed:
        avg_success_rate = sum(t.success_rate for t in completed) / len(completed)
        avg_response_time = sum(t.avg_response_time for t in completed) / len(completed)
    else:
        avg_success_rate = 0
        avg_response_time = 0

    return {
        "total_tests": total_tests,
        "completed_tests": completed_tests,
        "failed_tests": failed_tests,
        "running_tests": running_tests,
        "average_success_rate": round(avg_success_rate, 2),
        "average_response_time": round(avg_response_time, 2),
    }


@app.delete("/db/tests/{test_id}")
async def delete_test_from_db(test_id: str):
    """Delete a test record from database."""
    try:
        test = await LoadTest.get(test_id=test_id)
        await test.delete()
        return {"message": f"Test {test_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Test not found: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 70)
    print("🚀 Load Testing Dashboard Starting...")
    print("=" * 70)
    print("\n✨ Open your browser and visit:")
    print("   🌐 http://localhost:8000")
    print("\n📚 API Documentation:")
    print("   📊 Swagger: http://localhost:8000/docs")
    print("   📚 ReDoc: http://localhost:8000/redoc")
    print("\n" + "=" * 70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
