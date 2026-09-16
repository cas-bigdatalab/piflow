"""Resolve task references against durable, user/session-scoped history, not LLM memory."""
import re

from .feedback import ForecastError
from .schema import Intent


class TaskChoice(Exception):
    def __init__(self, options, pending, chosen, remaining):
        self.options, self.pending, self.chosen, self.remaining = options, pending, chosen, remaining


class TaskHistory:
    def __init__(self, store):
        self.store = store

    def list(self, session):
        tasks = self.store.list_tasks(session)
        # Old rows predate created_at. Recover submission time from persisted turns.
        if any(not t.get("created_at") for t in tasks):
            created = {}
            for turn in self.store.list_turns(session):
                run_id = turn["response"].get("run_id")
                if run_id and turn.get("created_at"):
                    created.setdefault(run_id, turn["created_at"])
            tasks = [{**t, "created_at": t.get("created_at") or created.get(t["run_id"], t["updated_at"])} for t in tasks]
        return sorted(tasks, key=lambda t: (t["created_at"], t["run_id"]))

    @staticmethod
    def summary(task):
        return {**{k: task.get(k) for k in ("run_id", "created_at", "status", "params")},
                "analysis_status": task.get("analysis_status", "not_generated")}

    def resolve(self, session, intent, *, pending=None):
        tasks = self.list(session)
        owned = {t["run_id"]: t for t in tasks}
        ids = list(intent.run_ids)
        if len(set(ids)) != len(ids):
            raise ForecastError("invalid_parameters", "请选择不同的任务进行比较。")
        if any(i not in owned for i in ids):
            raise ForecastError("task_not_found")
        references = list(intent.references)
        if pending:
            ids = [*pending["chosen"], *ids]
            references = [*references, *pending["remaining"]]
        for n, ref in enumerate(references):
            if isinstance(ref, dict):
                from .schema import TaskReference
                ref = TaskReference.model_validate(ref)
            candidates = [t for t in tasks if t["run_id"] not in ids
                and (ref.created_date is None or t["created_at"][:10] == ref.created_date.isoformat())
                and (ref.case_id is None or ref.case_id in t.get("params", {}).get("case_ids", []))
                and (ref.horizon_hours is None or ref.horizon_hours == t.get("params", {}).get("horizon_hours"))]
            if not candidates:
                raise ForecastError("task_not_found")
            if ref.order == "match" and len(candidates) > 1:
                raise TaskChoice([self.summary(t) for t in candidates], intent.model_dump(mode="json"), ids,
                                 [r.model_dump(mode="json") if hasattr(r, "model_dump") else r for r in references[n + 1:]])
            ordered = candidates[::-1] if ref.order == "latest" else candidates
            if ref.index > len(ordered):
                raise ForecastError("task_not_found")
            ids.append(ordered[ref.index - 1]["run_id"])
        if not ids:
            eligible = [t for t in tasks if intent.action not in {"explain", "report", "compare"} or t["status"] == "completed"]
            ids = [t["run_id"] for t in eligible[-(2 if intent.action == "compare" else 1):]]
        required = 2 if intent.action == "compare" else 1
        if len(ids) != required or len(set(ids)) != required:
            raise ForecastError("task_not_found", "需要两个不同的已完成任务才能比较。" if required == 2 else None)
        return [owned[i] for i in ids]

    @staticmethod
    def answer(message, pending):
        if not pending:
            return None
        text = message.strip().rstrip("。")
        options = pending["options"]
        match = re.fullmatch(r"(?:选择|选|就选)?\s*第?\s*([一二三四五六七八九十]|\d+)\s*(?:个|项)?", text)
        choice = {"run_id": text} if text in pending["candidate_ids"] else None
        if match:
            index = int(match[1]) if match[1].isdigit() else "一二三四五六七八九十".index(match[1]) + 1
            if 1 <= index <= len(options):
                choice = options[index - 1]
        if choice:
            return Intent.model_validate({**pending["intent"], "run_ids": [choice["run_id"]], "references": []})
        return None
