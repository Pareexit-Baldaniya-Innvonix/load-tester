"""
Database models for load testing using Tortoise-ORM.
"""

from tortoise import fields
from tortoise.models import Model
from datetime import datetime


class LoadTest(Model):
    """Model to store load test requests and results."""

    id = fields.IntField(pk=True)
    test_id = fields.CharField(max_length=100, unique=True, index=True)
    url = fields.CharField(max_length=500)
    status = fields.CharField(
        max_length=20,
        choices=("pending", "running", "completed", "failed"),
        default="pending",
    )

    # Test parameters
    duration = fields.IntField()
    num_users = fields.IntField()
    ramp_rate = fields.FloatField()

    # Results (stored as JSON for flexibility)
    total_requests = fields.IntField(null=True)
    total_failures = fields.IntField(null=True)
    success_rate = fields.FloatField(null=True)
    avg_response_time = fields.FloatField(null=True)
    median_response_time = fields.FloatField(null=True)
    p95_response_time = fields.FloatField(null=True)
    p99_response_time = fields.FloatField(null=True)

    # File paths
    html_report = fields.CharField(max_length=255, null=True)
    csv_file = fields.CharField(max_length=255, null=True)

    # Error info
    error_message = fields.TextField(null=True)

    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True)
    started_at = fields.DatetimeField(null=True)
    completed_at = fields.DatetimeField(null=True)

    class Meta:
        table = "load_tests"

    def __str__(self):
        return f"LoadTest({self.test_id} - {self.status})"


class TestMetrics(Model):
    """Model to store detailed test metrics over time."""

    id = fields.IntField(pk=True)
    load_test = fields.ForeignKeyField("src.LoadTest", related_name="metrics")

    elapsed_seconds = fields.IntField()
    users_count = fields.IntField()
    requests_per_second = fields.FloatField()

    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "test_metrics"

    def __str__(self):
        return f"Metrics({self.load_test.test_id} at {self.elapsed_seconds}s)"
