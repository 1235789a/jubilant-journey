from __future__ import annotations

from dataclasses import dataclass

from .models import AdapterMaturity, Asset, Platform, RuleStatus, VerticalPriority


MATURITY_AUTOMATION = {
    AdapterMaturity.P0: 0.0,
    AdapterMaturity.P1: 40.0,
    AdapterMaturity.P2: 75.0,
    AdapterMaturity.P3: 100.0,
}


def platform_score(asset: Asset, platform: Platform) -> float:
    scores = asset.metadata.get("platform_scores", {}).get(platform.platform_id, {})
    traffic = platform.natural_traffic_score
    monetization = float(scores.get("monetization", 50))
    fit = float(scores.get("fit", 70 if asset.vertical_id in platform.verticals_supported else 0))
    automation = MATURITY_AUTOMATION[platform.adapter_maturity]
    maintenance = float(scores.get("maintenance", 60))
    risk_default = 80 if platform.rule_status is RuleStatus.VERIFIED else 35
    risk = float(scores.get("risk", risk_default))
    total = (
        traffic * 0.30
        + monetization * 0.25
        + fit * 0.15
        + automation * 0.15
        + maintenance * 0.10
        + risk * 0.05
    )
    return round(max(0.0, min(100.0, total)), 2)


@dataclass(frozen=True, slots=True)
class VerticalEvaluation:
    score: float
    priority: VerticalPriority
    components: dict[str, float]


def evaluate_vertical(
    *,
    natural_traffic: float,
    ai_automation: float,
    monetization_distance: float,
    multi_platformability: float,
    multi_productability: float,
    maintenance_cost: float,
    legal_risk: float,
) -> VerticalEvaluation:
    components = {
        "natural_traffic": natural_traffic,
        "ai_automation": ai_automation,
        "monetization_distance": monetization_distance,
        "multi_platformability": multi_platformability,
        "multi_productability": multi_productability,
        "maintenance_cost": maintenance_cost,
        "legal_risk": legal_risk,
    }
    score = round(
        natural_traffic * 0.25
        + ai_automation * 0.20
        + monetization_distance * 0.15
        + multi_platformability * 0.15
        + multi_productability * 0.10
        + maintenance_cost * 0.10
        + legal_risk * 0.05,
        2,
    )
    if score >= 80:
        priority = VerticalPriority.P0
    elif score >= 65:
        priority = VerticalPriority.P1
    elif score >= 50:
        priority = VerticalPriority.P2
    else:
        priority = VerticalPriority.REJECT
    return VerticalEvaluation(score=score, priority=priority, components=components)
