from __future__ import annotations

from dataclasses import dataclass
from statistics import quantiles

from .database import Database
from .models import Metric, Recommendation, new_id, utc_now
from .registry import Registry


@dataclass(frozen=True, slots=True)
class YieldWeights:
    revenue: float = 1.0
    traffic: float = 0.01
    users: float = 0.25
    geo_brand: float = 0.5
    strategic: float = 0.5
    token_cost: float = 1.0
    human_time: float = 0.5
    maintenance: float = 1.0
    platform_cost: float = 1.0
    risk_cost: float = 1.0


def calculate_yield_score(
    *,
    revenue_value: float,
    traffic_value: float,
    user_value: float,
    geo_brand_value: float,
    strategic_value: float,
    token_cost: float,
    human_time_cost: float,
    maintenance_cost: float,
    platform_cost: float,
    risk_cost: float,
    weights: YieldWeights | None = None,
) -> float:
    w = weights or YieldWeights()
    numerator = (
        revenue_value * w.revenue
        + traffic_value * w.traffic
        + user_value * w.users
        + geo_brand_value * w.geo_brand
        + strategic_value * w.strategic
    )
    denominator = (
        token_cost * w.token_cost
        + human_time_cost * w.human_time
        + maintenance_cost * w.maintenance
        + platform_cost * w.platform_cost
        + risk_cost * w.risk_cost
    )
    return round(numerator / max(1.0, denominator), 4)


class AnalyticsService:
    def __init__(self, database: Database, registry: Registry):
        self.db = database
        self.registry = registry

    def aggregate(self) -> dict[str, float]:
        metrics = self.registry.list_metrics()
        keys = [
            "impressions",
            "views",
            "clicks",
            "downloads",
            "installs",
            "active_users",
            "followers",
            "subscribers",
            "engagement",
            "conversion",
            "revenue",
            "refunds",
            "cost",
            "token_cost",
            "human_minutes",
        ]
        result = {key: 0.0 for key in keys}
        for metric in metrics:
            for key in keys:
                result[key] += float(getattr(metric, key) or 0.0)
        result["metric_records"] = float(len(metrics))
        return result

    def token_summary(self) -> dict[str, float]:
        row = self.db.fetch_one(
            """
            SELECT COALESCE(SUM(input_tokens),0) AS input_tokens,
                   COALESCE(SUM(output_tokens),0) AS output_tokens,
                   COALESCE(SUM(cached_tokens),0) AS cached_tokens,
                   COALESCE(SUM(estimated_cost),0) AS estimated_cost
            FROM token_usage
            """
        )
        publications = max(
            1,
            int(self.db.fetch_one("SELECT COUNT(*) AS n FROM publications")["n"]),
        )
        assets = max(1, int(self.db.fetch_one("SELECT COUNT(*) AS n FROM assets")["n"]))
        revenue = max(1.0, self.aggregate()["revenue"])
        total = float(row["input_tokens"] + row["output_tokens"])
        return {
            "input_tokens": float(row["input_tokens"]),
            "output_tokens": float(row["output_tokens"]),
            "cached_tokens": float(row["cached_tokens"]),
            "total_tokens": total,
            "estimated_cost": round(float(row["estimated_cost"]), 4),
            "tokens_per_asset": round(total / assets, 2),
            "tokens_per_publication": round(total / publications, 2),
            "tokens_per_revenue": round(total / revenue, 2),
        }

    def record_token_usage(
        self,
        *,
        provider: str,
        model: str,
        task: str,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0,
        estimated_cost: float = 0.0,
        asset_id: str | None = None,
        job_id: str | None = None,
    ) -> str:
        usage_id = new_id("tok")
        self.db.execute(
            """
            INSERT INTO token_usage(
                usage_id, timestamp, provider, model, task, input_tokens,
                output_tokens, cached_tokens, estimated_cost, asset_id, job_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                usage_id,
                utc_now(),
                provider,
                model,
                task,
                input_tokens,
                output_tokens,
                cached_tokens,
                estimated_cost,
                asset_id,
                job_id,
            ),
        )
        return usage_id

    def record_human_time(
        self,
        *,
        task: str,
        human_minutes: float,
        asset_id: str | None = None,
        job_id: str | None = None,
        notes: str = "",
    ) -> str:
        entry_id = new_id("human")
        self.db.execute(
            """
            INSERT INTO human_time(
                entry_id, timestamp, task, human_minutes, asset_id, job_id, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (entry_id, utc_now(), task, human_minutes, asset_id, job_id, notes),
        )
        return entry_id

    @staticmethod
    def recommendation(score: float, consecutive_low_periods: int = 0) -> Recommendation:
        if score >= 5:
            return Recommendation.DOUBLE_DOWN
        if score >= 2:
            return Recommendation.KEEP
        if score >= 1:
            return Recommendation.WATCH
        if score >= 0.5:
            return Recommendation.REDUCE
        if consecutive_low_periods >= 3:
            return Recommendation.KILL_CANDIDATE
        return Recommendation.PAUSE
