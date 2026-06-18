
import threading

import deepagents.backends.filesystem as filesystem_backend_module


_PATCH_LOCK = threading.Lock()
_PATCHED = False


def install_deepagents_filesystem_utf8_compat() -> None:
    global _PATCHED

    with _PATCH_LOCK:
        if _PATCHED:
            return

        original_run = filesystem_backend_module.subprocess.run

        def utf8_safe_run(*args, **kwargs):
            if kwargs.get("text"):
                kwargs.setdefault("encoding", "utf-8")
                kwargs.setdefault("errors", "replace")

            result = original_run(*args, **kwargs)
            if kwargs.get("text"):
                if getattr(result, "stdout", None) is None:
                    result.stdout = ""
                if getattr(result, "stderr", None) is None:
                    result.stderr = ""
            return result

        filesystem_backend_module.subprocess.run = utf8_safe_run
        _PATCHED = True
