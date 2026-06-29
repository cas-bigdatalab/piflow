#!/usr/bin/env python3
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_piflow_skill import build_rewrite_followup_suggestion


class GenerateFollowupTests(unittest.TestCase):
    def test_build_rewrite_followup_suggestion_uses_default_message(self):
        result = build_rewrite_followup_suggestion(
            skill_name="demo_skill",
            skill_dir="workspace/skills/generated/demo_skill",
            rewrite_followup_hint="",
        )

        self.assertEqual(result["skill_name"], "demo_skill")
        self.assertEqual(result["skill_dir"], "workspace/skills/generated/demo_skill")
        self.assertIn("新的成功流程", result["message"])
        self.assertIn("rewrite_piflow_skill.py", result["command"])

    def test_build_rewrite_followup_suggestion_prefers_custom_hint(self):
        result = build_rewrite_followup_suggestion(
            skill_name="demo_skill",
            skill_dir="workspace/skills/generated/demo_skill",
            rewrite_followup_hint="如果后续流程更合适，可以继续按新流程改写。",
        )

        self.assertEqual(result["message"], "如果后续流程更合适，可以继续按新流程改写。")


if __name__ == "__main__":
    unittest.main()
