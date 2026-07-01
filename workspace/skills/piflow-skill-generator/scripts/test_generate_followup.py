#!/usr/bin/env python3
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_piflow_skill import build_rewrite_followup_suggestion


class GenerateFollowupTests(unittest.TestCase):
    def test_build_rewrite_followup_suggestion_uses_workspace_relative_skill_dir(self):
        result = build_rewrite_followup_suggestion(
            skill_name="demo_skill",
            skill_dir="skills/generated/demo_skill",
            rewrite_followup_hint="",
        )

        self.assertEqual(result["skill_name"], "demo_skill")
        self.assertEqual(result["skill_dir"], "skills/generated/demo_skill")
        self.assertIn("rewrite_piflow_skill.py", result["command"])
        self.assertNotIn("workspace/skills/generated", result["command"])

    def test_build_rewrite_followup_suggestion_prefers_custom_hint(self):
        result = build_rewrite_followup_suggestion(
            skill_name="demo_skill",
            skill_dir="skills/generated/demo_skill",
            rewrite_followup_hint="follow the newer successful flow if needed",
        )

        self.assertEqual(result["message"], "follow the newer successful flow if needed")


if __name__ == "__main__":
    unittest.main()
