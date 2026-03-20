---
name: flow_run
description: Run assembled flow payloads after user confirmation (for example, "start execution" or "run"). Use this skill to accept flow session payloads (`flow_session_id` or `flow_json_text`) and submit execution returning a process id.
allowed-tools:
  - run_flow
---

# flow_run

Accept assembled flow payload input and trigger execution submission.
Return a process id as the run receipt.
