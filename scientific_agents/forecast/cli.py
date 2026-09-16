"""Deployment checks and one real forecast, without starting another service."""
import argparse
import json
import uuid
import sys

from . import bootstrap  # noqa: F401
from .config import load_settings
from .model import create_predictor
from .providers import Registry
from .schema import TaskParams
from .workflow import ForecastWorkflow


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "check-data", "run"])
    parser.add_argument("--config")
    parser.add_argument("--case", action="append", default=None)
    parser.add_argument("--auxiliary-case", action="append", default=[])
    parser.add_argument("--origin")
    parser.add_argument("--hours", type=int)
    args = parser.parse_args()
    cfg = load_settings(args.config)
    model = create_predictor(cfg)
    registry = Registry(cfg)
    summary = registry.refresh()
    if args.command == "check":
        print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
        if any(s["state"] == "error" for s in summary["sources"]):
            raise ValueError("部分数据源刷新失败，请检查上面的源状态")
        from .resource_provider import manifest
        from .files import safe_path, verify
        for source in cfg.sources:
            if source.kind == "local_csv":
                directory, spec = manifest(source, cfg)
                for name, expected in spec["files"].items():
                    verify(safe_path(directory, name), expected)
                for case in source.cases:
                    for variable in [case.target, *case.covariates]:
                        registry.read(case.id, variable)
                print(f"数据校验通过：{source.id} ({len(source.cases)} cases)", flush=True)
        model.warmup()
        print(json.dumps(model.metadata(), ensure_ascii=False, indent=2))
        return
    if not args.case or not args.origin or args.hours is None:
        parser.error("check-data/run必须指定--case、--origin、--hours")
    workflow = ForecastWorkflow(cfg, registry, model)
    params = TaskParams(case_ids=args.case, auxiliary_case_ids=args.auxiliary_case, origin=args.origin, horizon_hours=args.hours)
    if args.command == "run":
        run_id = "fc-" + uuid.uuid4().hex[:24]
        result = workflow.run(run_id, params, lambda stage, status: print(stage, status, flush=True))
        print(cfg.root / "runs" / result.run_id / "report.html")
        return
    prepared = workflow.prepare(params)
    if args.command == "check-data":
        print(json.dumps([{k: item[k] for k in ["case_id", "unit", "quality", "provenance"]} for item in prepared], ensure_ascii=False, indent=2))
        return


if __name__ == "__main__":
    main()
