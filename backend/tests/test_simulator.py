"""Tests for the simulator ProcessManager and protocol runners."""

import os
import signal
import time
from unittest.mock import MagicMock, patch

import pytest

from devices.models import Device
from simulator.ethernetip_sim import _build_argv
from simulator.modbus_sim import _build_sim_device
from simulator.process_manager import ProcessManager
from pymodbus.simulator.simdata import DataType, SimData
from pymodbus.simulator.simdevice import SimDevice


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_device(protocol: str = "modbus", status: str = "stopped", pid: int | None = None) -> Device:
    config = {"unit_id": 1, "registers": []} if protocol == "modbus" else {"tags": []}
    port = 5020 if protocol == "modbus" else 44818
    device = Device.objects.create(
        name=f"sim-test-{protocol}-{os.getpid()}",
        protocol=protocol,
        port=port,
        config=config,
        status=status,
        pid=pid,
    )
    return device


# ---------------------------------------------------------------------------
# Modbus SimDevice builder (pymodbus 3.13 new API)
# ---------------------------------------------------------------------------

class TestModbusSimDeviceBuilder:
    def test_empty_config_builds_without_error(self) -> None:
        dev = _build_sim_device({"unit_id": 1, "registers": []})
        assert isinstance(dev, SimDevice)
        assert dev.id == 1

    def test_unit_id_propagated(self) -> None:
        dev = _build_sim_device({"unit_id": 5, "registers": []})
        assert dev.id == 5

    def test_holding_register_in_simdata(self) -> None:
        dev = _build_sim_device({
            "registers": [{"address": 10, "value": 42, "type": "holding"}]
        })
        # simdata is (di, co, ir, hr) — hr is index 3
        di_list, co_list, ir_list, hr_list = dev.simdata
        hr_entry = next((s for s in hr_list if s.address == 10), None)
        assert hr_entry is not None
        assert hr_entry.values == 42

    def test_coil_in_simdata(self) -> None:
        dev = _build_sim_device({
            "registers": [{"address": 0, "value": 1, "type": "coil"}]
        })
        di_list, co_list, ir_list, hr_list = dev.simdata
        co_entry = next((s for s in co_list if s.address == 0), None)
        assert co_entry is not None
        assert co_entry.values == 1

    def test_multiple_register_types(self) -> None:
        dev = _build_sim_device({
            "registers": [
                {"address": 0, "value": 1, "type": "holding"},
                {"address": 1, "value": 2, "type": "input"},
                {"address": 2, "value": 1, "type": "coil"},
                {"address": 3, "value": 0, "type": "discrete"},
            ]
        })
        di_list, co_list, ir_list, hr_list = dev.simdata
        assert any(s.address == 0 for s in hr_list)
        assert any(s.address == 1 for s in ir_list)
        assert any(s.address == 2 for s in co_list)
        assert any(s.address == 3 for s in di_list)


# ---------------------------------------------------------------------------
# EthernetIP argv builder
# ---------------------------------------------------------------------------

class TestEthernetIPArgvBuilder:
    def test_tags_appear_in_argv(self) -> None:
        config = {"tags": [{"name": "Pressure", "type": "REAL", "value": 0}]}
        argv = _build_argv(config, 44818)
        assert "--address" in argv
        assert ":44818" in argv
        assert "Pressure=REAL" in argv

    def test_empty_tags_uses_dummy(self) -> None:
        argv = _build_argv({"tags": []}, 44818)
        # Should contain the dummy tag to satisfy cpppo's requirement
        assert any("=" in arg for arg in argv)

    def test_multiple_tags(self) -> None:
        config = {
            "tags": [
                {"name": "Tag1", "type": "DINT", "value": 0},
                {"name": "Tag2", "type": "BOOL", "value": False},
            ]
        }
        argv = _build_argv(config, 44818)
        assert "Tag1=DINT" in argv
        assert "Tag2=BOOL" in argv

    def test_no_udp_flag_present(self) -> None:
        argv = _build_argv({"tags": []}, 44818)
        assert "--no-udp" in argv


# ---------------------------------------------------------------------------
# ProcessManager unit tests (mocked subprocesses)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestProcessManagerStartStop:
    def test_start_sets_running_status_and_pid(self) -> None:
        device = _make_device()
        mock_proc = MagicMock()
        mock_proc.pid = 99999

        pm = ProcessManager()
        with patch("simulator.process_manager.subprocess.Popen", return_value=mock_proc):
            pm.start_device(device)

        device.refresh_from_db()
        assert device.status == Device.Status.RUNNING
        assert device.pid == 99999

    def test_start_raises_if_already_running(self) -> None:
        device = _make_device(status="running", pid=12345)
        pm = ProcessManager()
        with pytest.raises(RuntimeError, match="already running"):
            pm.start_device(device)

    def test_stop_sends_sigterm_and_clears_pid(self) -> None:
        device = _make_device(status="running", pid=99998)
        pm = ProcessManager()

        with patch.object(pm, "_terminate") as mock_term:
            pm.stop_device(device)
            mock_term.assert_called_once_with(99998, device.name)

        device.refresh_from_db()
        assert device.status == Device.Status.STOPPED
        assert device.pid is None

    def test_stop_handles_already_dead_process(self) -> None:
        device = _make_device(status="running", pid=99997)
        pm = ProcessManager()

        # _terminate should not raise even if pid doesn't exist
        with patch("simulator.process_manager.ProcessManager._is_alive", return_value=False):
            pm.stop_device(device)

        device.refresh_from_db()
        assert device.status == Device.Status.STOPPED


@pytest.mark.django_db
class TestHealthCheck:
    def test_running_device_with_alive_pid_returns_running(self) -> None:
        device = _make_device(status="running", pid=os.getpid())  # use own PID — always alive
        pm = ProcessManager()
        result = pm.health_check(device)
        assert result == Device.Status.RUNNING

    def test_running_device_with_dead_pid_marks_error(self) -> None:
        device = _make_device(status="running", pid=99996)
        pm = ProcessManager()

        with patch("simulator.process_manager.ProcessManager._is_alive", return_value=False):
            result = pm.health_check(device)

        assert result == Device.Status.ERROR
        device.refresh_from_db()
        assert device.status == Device.Status.ERROR
        assert device.pid is None

    def test_stopped_device_returns_stopped_without_pid_check(self) -> None:
        device = _make_device(status="stopped")
        pm = ProcessManager()
        with patch("simulator.process_manager.ProcessManager._is_alive") as mock_alive:
            result = pm.health_check(device)
            mock_alive.assert_not_called()
        assert result == Device.Status.STOPPED


@pytest.mark.django_db
class TestReconcileOnStartup:
    def test_resets_running_device_with_dead_pid(self) -> None:
        device = _make_device(status="running", pid=99995)
        pm = ProcessManager()

        with patch("simulator.process_manager.ProcessManager._is_alive", return_value=False):
            pm.reconcile_on_startup()

        device.refresh_from_db()
        assert device.status == Device.Status.ERROR
        assert device.pid is None

    def test_leaves_running_device_with_live_pid_intact(self) -> None:
        device = _make_device(status="running", pid=os.getpid())
        pm = ProcessManager()
        pm.reconcile_on_startup()

        device.refresh_from_db()
        assert device.status == Device.Status.RUNNING

    def test_resets_starting_device_with_dead_pid(self) -> None:
        device = _make_device(status="starting", pid=99994)
        pm = ProcessManager()

        with patch("simulator.process_manager.ProcessManager._is_alive", return_value=False):
            pm.reconcile_on_startup()

        device.refresh_from_db()
        assert device.status == Device.Status.ERROR


# ---------------------------------------------------------------------------
# Integration smoke test — real Modbus server (skipped in CI if flagged)
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.django_db
class TestModbusIntegration:
    """Start a real Modbus server subprocess, connect to it, read a register.

    Run with:  uv run pytest -m integration backend/tests/test_simulator.py
    """

    def test_modbus_server_starts_and_responds(self) -> None:
        import asyncio

        import pymodbus.client as mb_client

        config = {
            "unit_id": 1,
            "registers": [{"address": 100, "value": 777, "type": "holding"}],
        }
        port = 5090  # Use a port not in the normal allocation range

        pm = ProcessManager()

        # Use a temporary Device-like object to avoid DB port constraints
        device = Device.objects.create(
            name="integration-modbus",
            protocol=Device.Protocol.MODBUS,
            port=port,
            config=config,
        )
        try:
            pm.start_device(device)
            time.sleep(1.0)  # Give the server time to bind

            async def _read() -> int:
                client = mb_client.AsyncModbusTcpClient("127.0.0.1", port=port)
                await client.connect()
                result = await client.read_holding_registers(100, count=1, slave=1)
                await client.close()
                return result.registers[0]

            value = asyncio.run(_read())
            assert value == 777
        finally:
            pm.stop_device(device)
            device.delete()
