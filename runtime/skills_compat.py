import threading

import deepagents.middleware.skills as skills_module


_PATCH_LOCK = threading.Lock()
_PATCHED = False


def install_deepagents_skills_refresh_compat() -> None:
    global _PATCHED

    with _PATCH_LOCK:
        if _PATCHED:
            return

        original_before_agent = skills_module.SkillsMiddleware.before_agent
        original_abefore_agent = skills_module.SkillsMiddleware.abefore_agent

        def before_agent(self, state, runtime, config):  # noqa: ANN001
            state.pop("skills_metadata", None)
            return original_before_agent(self, state, runtime, config)

        async def abefore_agent(self, state, runtime, config):  # noqa: ANN001
            state.pop("skills_metadata", None)
            return await original_abefore_agent(self, state, runtime, config)

        skills_module.SkillsMiddleware.before_agent = before_agent
        skills_module.SkillsMiddleware.abefore_agent = abefore_agent
        _PATCHED = True
