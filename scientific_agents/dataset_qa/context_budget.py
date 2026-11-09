"""Local token accounting and recoverable model views, independent of MCP execution."""
from collections import OrderedDict
from hashlib import sha256
import math

from .context import encode

class TokenCounter:
    """Use an explicitly matched tokenizer, or a labelled, usage-calibrated estimate.

    The fallback is deliberately more conservative than the usual four ASCII
    characters per token and accounts separately for Unicode. It is NOT an exact
    tokenizer or a guaranteed upper bound. Request framing and output are reserved
    separately; provider rejections still have a bounded recovery path.
    """

    def __init__(self, tokenizer_path=None):
        self.tokenizer = None
        self.mode = "unicode_estimate"
        self.scale = 1.0
        self.cache = OrderedDict()
        if tokenizer_path:
            # Loading an explicitly configured file is local-only. An invalid
            # configuration must not silently pretend to be an exact counter.
            from tokenizers import Tokenizer
            self.tokenizer = Tokenizer.from_file(tokenizer_path)
            self.tokenizer.no_truncation()
            self.tokenizer.no_padding()
            self.mode = "local_tokenizer"

    def __call__(self, text):
        raw = text.encode("utf-8")
        key = sha256(raw).digest()
        value = self.cache.get(key)
        if value is None:
            if self.tokenizer is not None:
                value = len(self.tokenizer.encode(text, add_special_tokens=False).ids)
            else:
                ascii_size = len(text.encode("ascii", errors="ignore"))
                value = math.ceil(ascii_size/3 + (len(raw)-ascii_size)/2)
            self.cache[key] = value
            if len(self.cache)>256:
                self.cache.popitem(last=False)
        else:
            self.cache.move_to_end(key)
        return math.ceil(value*self.scale)

    def observe(self, estimated, actual, *, request_scale=None):
        # Only correct upwards: a short English reply must not lower the safety
        # allowance for a later Unicode/schema-heavy request. No message text is
        # retained in the cache or usage logs.
        if self.tokenizer is None and estimated>0 and isinstance(actual, int) and not isinstance(actual, bool) and actual>estimated:
            scale = self.scale if request_scale is None else request_scale
            self.scale = max(self.scale, scale*actual/estimated*1.10)


def context_overflow(error):
    """Recognize length rejections, never retry unrelated HTTP 400s or failures."""
    if getattr(error, "code", None)=="context_too_large":
        return True
    if getattr(error, "status_code", None) not in {400, 413, 422}:
        return False
    body = getattr(error, "body", None)
    detail = body.get("error", body) if isinstance(body, dict) else {}
    if not isinstance(detail, dict):
        return False
    code = str(detail.get("code") or getattr(error, "code", "")).lower()
    if code in {"context_length_exceeded", "context_window_exceeded", "max_context_length_exceeded", "input_tokens_exceeded"}:
        return True
    message = str(detail.get("message", "")).lower()
    return any(term in message for term in (
        "maximum context length", "context window exceeded", "context length exceeded",
        "input length exceeds", "input length is too long", "input tokens length is too long",
        "range of input length should be", "prompt is too long", "too many input tokens",
    ))


def summary_batch(summary, messages, limit, max_single):
    """Select a contiguous prefix of WHOLE messages; never skip an oversized row."""
    selected = []
    for row in messages:
        proposed = [*selected, row]
        size = len(encode({"summary": summary, "messages": proposed}))
        if size>limit:
            # One long message may use more room, but is never silently sliced
            # and then marked completely summarized by the persistence cursor.
            if not selected and size<=max_single:
                selected = proposed
            break
        selected = proposed
    return selected


def recovery_evidence(payload, cards):
    """Preserve executable dependencies and expose checks against FULL artifacts."""
    from .contracts import QAError
    from .context import redact
    from .operations import Operations
    from .planning import Check
    from .references import at_path

    plan = payload.get("plan")
    if not plan:
        return {}
    operations = Operations(payload.get("operations", []))
    artifacts = {card["result_id"]: card for card in cards}
    outcomes = {value["key"]: value for value in plan["spec"]["outcomes"]}
    result = {}
    for step in plan["spec"]["steps"]:
        operation = operations.get(plan["operations"][step["key"]])
        contract = plan.get("contracts", {}).get(step["key"], {})
        checks = [*contract.get("requires", []), *contract.get("unavailable_when", []),
            *(check for key in step.get("produces", []) for check in outcomes[key].get("checks", []))]
        for rid in operations.result_ids(operation) if operation else []:
            if rid in artifacts and checks:
                result.setdefault(rid, {})["checks"] = [{**check,
                    "matched": Check.model_validate(check).matches(artifacts[rid].get("data"))} for check in checks]
        bindings = list(step.get("inputs", {}).values())
        if isinstance(step.get("object"), dict):
            bindings.append(step["object"])
        for binding in bindings:
            source = operations.get(plan["operations"][binding["step"]])
            for rid in operations.result_ids(source) if source else []:
                if rid not in artifacts:
                    continue
                try:
                    value = at_path(redact(artifacts[rid].get("data")), binding["path"])
                except QAError:
                    continue
                result.setdefault(rid, {}).setdefault("inputs", {})[binding["path"]] = value
    return result
