from __future__ import annotations

import argparse
import json
from pathlib import Path

from .application import Application
from .health import HealthMonitor
from .models import to_dict
from .seed import demo, seed


def _export(application: Application, destination: Path) -> None:
    payload = {
        "assets": application.registry.serialize_all(application.registry.list_assets()),
        "verticals": application.registry.serialize_all(
            application.registry.list_verticals()
        ),
        "platforms": application.registry.serialize_all(application.registry.list_platforms()),
        "accounts": application.registry.serialize_all(application.registry.list_accounts()),
        "jobs": application.registry.serialize_all(application.queue.list(100000)),
        "publications": application.registry.serialize_all(
            application.registry.list_publications()
        ),
        "variants": application.registry.serialize_all(
            application.registry.list_variants()
        ),
        "rules": application.registry.serialize_all(application.registry.list_rules()),
        "metrics": application.registry.serialize_all(application.registry.list_metrics()),
        "experiments": application.registry.serialize_all(
            application.registry.list_experiments()
        ),
        "human_reviews": application.registry.serialize_all(
            application.registry.list_reviews()
        ),
        "audit_logs": application.audit.recent(100000),
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="distribution-os")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Initialize SQLite and seed the 31-platform registry")
    sub.add_parser("demo", help="Run both end-to-end dry-run pilots")
    worker = sub.add_parser("worker", help="Process queued jobs")
    worker.add_argument("--max-jobs", type=int, default=100)
    sub.add_parser("health", help="Run health checks")
    sub.add_parser("tick", help="Enqueue and execute idempotent daily maintenance")
    backup = sub.add_parser("backup", help="Create and verify an online SQLite backup")
    backup.add_argument("destination", type=Path)
    export = sub.add_parser("export", help="Export non-secret system data")
    export.add_argument("destination", type=Path)
    serve = sub.add_parser("serve", help="Start the dashboard API")
    serve.add_argument("--host", default=None)
    serve.add_argument("--port", type=int, default=None)
    args = parser.parse_args()
    application = Application.create()

    if args.command == "init":
        print(json.dumps(seed(application), ensure_ascii=False, indent=2))
    elif args.command == "demo":
        print(json.dumps(demo(application), ensure_ascii=False, indent=2))
    elif args.command == "worker":
        jobs = application.worker.run_until_empty(args.max_jobs)
        print(json.dumps([to_dict(item) for item in jobs], ensure_ascii=False, indent=2))
    elif args.command == "health":
        print(json.dumps(HealthMonitor(application).run(), ensure_ascii=False, indent=2))
    elif args.command == "tick":
        seed(application)
        scheduled = application.scheduler.enqueue_daily()
        completed = application.worker.run_until_empty()
        print(
            json.dumps(
                {
                    "scheduled": [to_dict(item) for item in scheduled],
                    "completed": [to_dict(item) for item in completed],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.command == "backup":
        print(
            json.dumps(
                application.database.backup(args.destination),
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.command == "export":
        _export(application, args.destination)
        print(args.destination)
    elif args.command == "serve":
        host = args.host or application.settings.host
        port = args.port or application.settings.port
        try:
            import uvicorn
        except ModuleNotFoundError:
            from .stdlib_server import serve

            serve(application, host=host, port=port)
        else:
            uvicorn.run(
                "distribution_os.api:app",
                host=host,
                port=port,
                reload=False,
            )


if __name__ == "__main__":
    main()
