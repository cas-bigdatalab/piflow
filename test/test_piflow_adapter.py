import pytest

from runtime import piflow_adapter


def test_init_piflow_run_tracking_db_skips_when_cn_piflow_missing(monkeypatch, caplog):
    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "cn.piflow.runtime.store.postgres.schema":
            raise ModuleNotFoundError("No module named 'cn'", name="cn")
        return original_import(name, globals, locals, fromlist, level)

    def fail_get_connection():
        pytest.fail("database connection should not be opened when cn.piflow is unavailable")

    original_import = __import__
    monkeypatch.setattr("builtins.__import__", fake_import)
    monkeypatch.setattr(piflow_adapter, "log", piflow_adapter.log)
    monkeypatch.setattr("database.postgres.get_connection", fail_get_connection)

    with caplog.at_level("WARNING", logger="flow.engine"):
        piflow_adapter.init_piflow_run_tracking_db()

    assert "skip PiFlow run tracking schema initialization because reserved module is unavailable" in caplog.text
