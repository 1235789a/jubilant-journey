from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, TypeVar


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


class AssetStatus(StrEnum):
    IDEA = "IDEA"
    RESEARCHING = "RESEARCHING"
    BUILDING = "BUILDING"
    READY = "READY"
    PUBLISHING = "PUBLISHING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    KILLED = "KILLED"
    ARCHIVED = "ARCHIVED"
    BLOCKED = "BLOCKED"


class DistributionMode(StrEnum):
    WIDE = "WIDE"
    EXCLUSIVE = "EXCLUSIVE"
    HYBRID = "HYBRID"
    UNDECIDED = "UNDECIDED"


class RuleStatus(StrEnum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    OUTDATED = "OUTDATED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCKED_BY_AGE = "BLOCKED_BY_AGE"
    GUARDIAN_REQUIRED = "GUARDIAN_REQUIRED"
    BLOCKED_BY_REGION = "BLOCKED_BY_REGION"
    BLOCKED_BY_EXCLUSIVITY = "BLOCKED_BY_EXCLUSIVITY"
    BLOCKED_BY_POLICY = "BLOCKED_BY_POLICY"

    @classmethod
    def parse(cls, value: str) -> "RuleStatus":
        if value == "RULES_UNVERIFIED":
            value = "UNVERIFIED"
        return cls(value)


class AdapterMaturity(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class JobType(StrEnum):
    GENERATE = "GENERATE"
    ADAPT = "ADAPT"
    VALIDATE = "VALIDATE"
    PUBLISH = "PUBLISH"
    UPDATE = "UPDATE"
    FETCH_METRICS = "FETCH_METRICS"
    HEALTH_CHECK = "HEALTH_CHECK"
    RETRY = "RETRY"
    REVIEW = "REVIEW"
    ARCHIVE = "ARCHIVE"


class JobStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    WAITING_HUMAN = "WAITING_HUMAN"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"
    DEAD_LETTER = "DEAD_LETTER"


class ReviewLevel(StrEnum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"


class RouteDecision(StrEnum):
    ALLOW_DRY_RUN = "ALLOW_DRY_RUN"
    ALLOW_LIVE = "ALLOW_LIVE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCKED = "BLOCKED"
    ALREADY_PUBLISHED = "ALREADY_PUBLISHED"


class HealthStatus(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    BROKEN = "BROKEN"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    RULE_OUTDATED = "RULE_OUTDATED"


class Recommendation(StrEnum):
    DOUBLE_DOWN = "DOUBLE_DOWN"
    KEEP = "KEEP"
    WATCH = "WATCH"
    REDUCE = "REDUCE"
    PAUSE = "PAUSE"
    KILL_CANDIDATE = "KILL_CANDIDATE"


class VerticalPriority(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    REJECT = "REJECT"


@dataclass(slots=True)
class Asset:
    asset_id: str
    name: str
    vertical_id: str
    product_type: str
    status: AssetStatus
    master_source: str
    master_version: str
    language: str
    market: str
    category: str
    tags: list[str]
    distribution_mode: DistributionMode
    priority: int
    human_owner: str
    production_cost: float = 0.0
    token_cost: float = 0.0
    estimated_value: float = 0.0
    yield_score: float = 0.0
    quality_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass(slots=True)
class Vertical:
    vertical_id: str
    name: str
    status: str
    pilot_limit: int
    scores: dict[str, float]
    evaluated_score: float
    priority: VerticalPriority
    updated_at: str = field(default_factory=utc_now)


@dataclass(slots=True)
class Platform:
    platform_id: str
    platform_name: str
    verticals_supported: list[str]
    website: str
    official_docs: list[str]
    natural_traffic_score: float
    monetization_type: str
    distribution_type: str
    age_requirement: int | None
    guardian_supported: bool | None
    identity_verification_required: bool | None
    publisher_account_type: list[str]
    multi_product_allowed: bool | None
    multi_channel_allowed: bool | None
    duplicate_personal_account_allowed: bool
    exclusivity_rules: str
    ai_content_policy: str
    automation_policy: str
    api_available: bool | None
    cli_available: bool | None
    browser_automation_allowed: bool | None
    manual_only_actions: list[str]
    publishing_cost: float | None
    platform_fee: str
    revenue_share: str
    payout_method: list[str]
    payout_threshold: str
    country_restrictions: list[str]
    rate_limits: str
    content_limits: str
    review_process: str
    adapter_name: str | None
    adapter_version: str | None
    adapter_maturity: AdapterMaturity
    rule_status: RuleStatus
    rule_version: str
    last_verified_at: str | None
    live_publish: bool
    notes: str


@dataclass(slots=True)
class RuleRecord:
    rule_id: str
    platform_id: str
    rule_version: str
    status: RuleStatus
    scope: str
    evidence_urls: list[str]
    facts: dict[str, Any]
    verified_at: str | None
    notes: str
    created_at: str = field(default_factory=utc_now)


@dataclass(slots=True)
class Account:
    account_id: str
    platform_id: str
    account_type: str
    brand_name: str
    owner_type: str
    age_status: str
    status: str
    credential_reference: str | None
    channels: list[str]
    health_status: HealthStatus
    payout_ready: bool = False
    country: str = "UNKNOWN"
    created_at: str = field(default_factory=utc_now)
    last_login_at: str | None = None
    notes: str = ""


@dataclass(slots=True)
class Job:
    job_id: str
    asset_id: str | None
    platform_id: str | None
    account_id: str | None
    job_type: JobType
    priority: int
    status: JobStatus
    idempotency_key: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)
    scheduled_at: str = field(default_factory=utc_now)
    started_at: str | None = None
    finished_at: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    token_usage: int = 0
    error: str | None = None
    output_url: str | None = None
    logs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Publication:
    publication_id: str
    asset_id: str
    platform_id: str
    account_id: str
    asset_version: str
    content_hash: str
    status: str
    mode: str
    output_url: str | None
    adapter_version: str | None
    job_id: str
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    variant_id: str | None = None


@dataclass(slots=True)
class Variant:
    variant_id: str
    asset_id: str
    platform_id: str
    asset_version: str
    adapter_name: str
    adapter_version: str
    content_hash: str
    artifact_path: str
    status: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)


@dataclass(slots=True)
class Metric:
    metric_id: str
    asset_id: str
    platform_id: str
    timestamp: str
    impressions: float | None = None
    views: float | None = None
    clicks: float | None = None
    downloads: float | None = None
    installs: float | None = None
    active_users: float | None = None
    followers: float | None = None
    subscribers: float | None = None
    engagement: float | None = None
    conversion: float | None = None
    revenue: float | None = None
    refunds: float | None = None
    cost: float | None = None
    token_cost: float | None = None
    human_minutes: float | None = None
    source: str = "PLATFORM"


@dataclass(slots=True)
class Experiment:
    experiment_id: str
    hypothesis: str
    vertical: str
    platform: str
    start_date: str
    token_budget: float
    time_budget: float
    money_budget: float
    success_metric: str
    failure_metric: str
    result: str = "PENDING"
    decision: str = "WATCH"


@dataclass(slots=True)
class HumanReview:
    review_id: str
    job_id: str | None
    asset_id: str | None
    platform_id: str | None
    action: str
    reason: str
    status: str = "PENDING"
    risk_level: str = "HIGH"
    created_at: str = field(default_factory=utc_now)
    resolved_at: str | None = None


@dataclass(slots=True)
class RouteResult:
    decision: RouteDecision
    can_package: bool
    can_publish: bool
    score: float
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AdapterResult:
    status: str
    artifact_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _jsonable(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if is_dataclass(value):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def to_dict(value: Any) -> dict[str, Any]:
    result = _jsonable(value)
    if not isinstance(result, dict):
        raise TypeError("to_dict expects a dataclass or mapping")
    return result


def to_json(value: Any) -> str:
    return json.dumps(_jsonable(value), ensure_ascii=False, sort_keys=True)


T = TypeVar("T")


def dataclass_from_dict(cls: type[T], data: dict[str, Any]) -> T:
    known = {item.name for item in fields(cls)}
    return cls(**{key: value for key, value in data.items() if key in known})
