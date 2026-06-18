# from types import SimpleNamespace

# import deepagents.backends.filesystem as filesystem

# from runtime.deepagents_compat import install_deepagents_filesystem_utf8_compat


# def test_install_deepagents_filesystem_utf8_compat_forces_utf8_and_normalizes_stdout(monkeypatch):
#     seen = {}

#     def fake_run(*args, **kwargs):
#         seen.update(kwargs)
#         return SimpleNamespace(stdout=None, stderr=None)

#     monkeypatch.setattr(filesystem.subprocess, "run", fake_run)

#     install_deepagents_filesystem_utf8_compat()
#     result = filesystem.subprocess.run(["rg", "--json", "-F", "--", "清洗", "."], capture_output=True, text=True)

#     assert seen["encoding"] == "utf-8"
#     assert seen["errors"] == "replace"
#     assert result.stdout == ""
#     assert result.stderr == ""
