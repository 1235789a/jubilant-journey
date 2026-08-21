from __future__ import annotations

from dataclasses import dataclass, field

from .adapters import AdapterRegistry, BrowserExtensionAdapter, EbookAdapter
from .analytics import AnalyticsService
from .audit import AuditLogger
from .config import Settings
from .database import Database
from .distribution import DistributionService
from .jobs import JobQueue
from .registry import Registry
from .router import PlatformRouter, RuleEngine
from .safety import CircuitBreaker, KillSwitch
from .scheduler import MaintenanceScheduler
from .worker import Worker


@dataclass(slots=True)
class Application:
    settings: Settings
    database: Database
    registry: Registry
    audit: AuditLogger
    kill_switch: KillSwitch
    circuit_breaker: CircuitBreaker
    queue: JobQueue
    adapters: AdapterRegistry
    router: PlatformRouter
    distribution: DistributionService
    analytics: AnalyticsService
    scheduler: MaintenanceScheduler = field(init=False)
    worker: Worker = field(init=False)

    @classmethod
    def create(cls, settings: Settings | None = None) -> "Application":
        config = settings or Settings.from_env()
        config.ensure_directories()
        database = Database(config.database_path)
        database.initialize()
        registry = Registry(database)
        audit = AuditLogger(database)
        kill_switch = KillSwitch(database, audit)
        kill_switch.initialize()
        circuit_breaker = CircuitBreaker(database, config)
        queue = JobQueue(database, config, circuit_breaker)
        adapters = AdapterRegistry()
        adapters.register(BrowserExtensionAdapter())
        adapters.register(EbookAdapter())
        router = PlatformRouter(
            registry, config, RuleEngine(), kill_switch, circuit_breaker
        )
        distribution = DistributionService(
            settings=config,
            registry=registry,
            adapters=adapters,
            router=router,
            queue=queue,
            audit=audit,
        )
        analytics = AnalyticsService(database, registry)
        application = cls(
            settings=config,
            database=database,
            registry=registry,
            audit=audit,
            kill_switch=kill_switch,
            circuit_breaker=circuit_breaker,
            queue=queue,
            adapters=adapters,
            router=router,
            distribution=distribution,
            analytics=analytics,
        )
        application.scheduler = MaintenanceScheduler(application)
        application.worker = Worker(application)
        return application
