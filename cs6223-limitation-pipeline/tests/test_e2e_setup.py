"""`pipeline doctor` / `pipeline e2e` static checks: configuration comes from environment variables only."""
import os

import pytest

from pipeline import e2e as E

GOOD = {"SOCLAAS_API_KEY": "k" * 40, "SOCLAAS_BASE_URL": "https://host.example/v1", "SOCLAAS_IFACE": "eth0"}


def run(env, **kw):
    kw.setdefault("which", lambda n: "/usr/bin/" + n)
    kw.setdefault("iface_check", lambda i: None)
    return {c.name: c for c in E.check_environment(env, **kw)}


def test_good_configuration_has_no_failure():
    r = run(GOOD)
    assert r["SOCLAAS_API_KEY"].level == "ok" and r["SOCLAAS_BASE_URL"].level == "ok"
    assert r["SOCLAAS_IFACE"].level == "ok" and r["PIPELINE_MODEL"].detail == "x-test-2"


def test_key_value_is_never_printed():
    r = run({**GOOD, "SOCLAAS_API_KEY": "SECRETVALUE" + "x" * 30})
    assert all("SECRETVALUE" not in c.line() for c in r.values())


@pytest.mark.parametrize("key", ["", "   ", E.PLACEHOLDER_KEY, "has space"])
def test_bad_keys_fail(key):
    assert run({**GOOD, "SOCLAAS_API_KEY": key})["SOCLAAS_API_KEY"].level == "FAIL"


@pytest.mark.parametrize("url", ["", "host.example/v1", "ftp://host/v1", "http://127.0.0.1:8787/v1"])
def test_bad_base_urls_fail(url):
    assert run({**GOOD, "SOCLAAS_BASE_URL": url})["SOCLAAS_BASE_URL"].level == "FAIL"


def test_base_url_without_v1_only_warns():
    assert run({**GOOD, "SOCLAAS_BASE_URL": "https://host.example/api"})["SOCLAAS_BASE_URL"].level == "warn"


def test_missing_interface_fails_and_empty_means_ordinary_routing():
    assert run(GOOD, iface_check=lambda i: f"interface {i!r} not found")["SOCLAAS_IFACE"].level == "FAIL"
    r = run({**GOOD, "SOCLAAS_IFACE": ""}, iface_check=lambda i: pytest.fail("must not be called"))
    assert r["SOCLAAS_IFACE"].level == "ok"


def test_other_model_warns():
    assert run({**GOOD, "PIPELINE_MODEL": "other"})["PIPELINE_MODEL"].level == "warn"


def test_agent_and_paper_side_checks_only_when_asked():
    assert "bwrap" not in run(GOOD) and "node" not in run(GOOD)
    r = run(GOOD, agent=True, paper_side=True, which=lambda n: None)
    assert r["bwrap"].level == "FAIL" and r["node"].level == "FAIL"


def test_unknown_artifact_fails():
    assert run(GOOD, aid="no-such-paper")["artifact"].level == "FAIL"


def test_children_get_a_placeholder_key(monkeypatch):
    monkeypatch.setenv("SOCLAAS_API_KEY", "real")
    monkeypatch.setenv("SOCLAAS_BASE_URL", "https://host/v1")
    E.point_children_at_relay()
    assert os.environ["SOCLAAS_API_KEY"] == E.PLACEHOLDER_KEY and os.environ["SOCLAAS_BASE_URL"] == E.RELAY_URL
