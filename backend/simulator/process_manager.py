"""Manages simulator subprocesses: start, stop, health-check, reconcile."""

import json
import logging
import os
import pathlib
import signal
import subprocess
import sys
import time

log = logging.getLogger(__name__)

_RUNNER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runners")
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOG_DIR = pathlib.Path(_BACKEND_DIR) / "logs"

_RUNNER_SCRIPTS = {
    "modbus": os.path.join(_RUNNER_DIR, "modbus_runner.py"),
    "ethernetip": os.path.join(_RUNNER_DIR, "ethernetip_runner.py"),
}

# Seconds to wait for SIGTERM before sending SIGKILL.
_GRACEFUL_TIMEOUT = 5.0

# Maximum lines returned by read_logs().
_MAX_LOG_LINES = 500


def device_log_path(device_id: str) -> pathlib.Path:
    return _LOG_DIR / f"{device_id}.log"


class ProcessManager:
    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def start_device(self, device: object) -> None:
        """Launch a simulator subprocess for *device* and persist the PID."""
        from devices.models import Device

        assert isinstance(device, Device)

        if device.status == Device.Status.RUNNING:
            raise RuntimeError(f"Device {device.name!r} is already running")

        runner = _RUNNER_SCRIPTS.get(device.protocol)
        if runner is None:
            raise ValueError(f"No runner for protocol {device.protocol!r}")

        env = {
            **os.environ,
            "PYTHONPATH": _BACKEND_DIR + os.pathsep + os.environ.get("PYTHONPATH", ""),
            "SIM_PORT": str(device.port),
            "SIM_CONFIG": json.dumps(dict(device.config)),
        }

        _LOG_DIR.mkdir(exist_ok=True)
        log_path = device_log_path(str(device.id))
        # Open in append mode so logs survive across start/stop cycles.
        log_file = open(log_path, "a")  # noqa: WPS515 — file closed by child process

        proc = subprocess.Popen(
            [sys.executable, runner],
            env=env,
            stdout=log_file,
            stderr=log_file,
        )
        # Close the parent's copy of the fd; child keeps its own.
        log_file.close()

        log.info(
            "Started %s simulator for %r on port %d (pid=%d, log=%s)",
            device.protocol, device.name, device.port, proc.pid, log_path,
        )

        device.status = Device.Status.RUNNING
        device.pid = proc.pid
        device.save(update_fields=["status", "pid", "updated_at"])

    def stop_device(self, device: object) -> None:
        """Send SIGTERM to the simulator process, wait, then SIGKILL if needed."""
        from devices.models import Device

        assert isinstance(device, Device)

        if device.pid is not None:
            self._terminate(device.pid, device.name)

        device.status = Device.Status.STOPPED
        device.pid = None
        device.save(update_fields=["status", "pid", "updated_at"])

    def health_check(self, device: object) -> str:
        """Return current status, updating the DB if the process has died."""
        from devices.models import Device

        assert isinstance(device, Device)

        if device.status not in (Device.Status.RUNNING, Device.Status.STARTING):
            return device.status

        if device.pid is None or not self._is_alive(device.pid):
            log.warning(
                "Simulator process for %r (pid=%s) is no longer alive — marking error",
                device.name, device.pid,
            )
            device.status = Device.Status.ERROR
            device.pid = None
            device.save(update_fields=["status", "pid", "updated_at"])
            return Device.Status.ERROR

        return device.status

    def read_logs(self, device_id: str, lines: int = 100) -> list[str]:
        """Return the last *lines* lines from the device's log file."""
        lines = min(lines, _MAX_LOG_LINES)
        log_path = device_log_path(device_id)
        if not log_path.exists():
            return []
        text = log_path.read_text(errors="replace")
        all_lines = text.splitlines()
        return all_lines[-lines:]

    def reconcile_on_startup(self) -> None:
        """Reset devices that appear running but whose PID is dead."""
        from devices.models import Device

        stale = Device.objects.filter(
            status__in=[Device.Status.RUNNING, Device.Status.STARTING]
        )
        for device in stale:
            if device.pid is None or not self._is_alive(device.pid):
                log.warning(
                    "Reconcile: resetting stale device %r (pid=%s) to 'error'",
                    device.name, device.pid,
                )
                device.status = Device.Status.ERROR
                device.pid = None
                device.save(update_fields=["status", "pid", "updated_at"])

    def shutdown_all(self) -> None:
        """Kill all running simulator processes. Registered as an atexit handler."""
        from devices.models import Device

        running = Device.objects.filter(status=Device.Status.RUNNING).exclude(pid=None)
        for device in running:
            log.info("Shutdown: terminating simulator for %r (pid=%d)", device.name, device.pid)
            self._terminate(device.pid, device.name)
            device.status = Device.Status.STOPPED
            device.pid = None
            device.save(update_fields=["status", "pid", "updated_at"])

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _is_alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False

    def _terminate(self, pid: int, name: str = "") -> None:
        if not self._is_alive(pid):
            return
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            return

        deadline = time.monotonic() + _GRACEFUL_TIMEOUT
        while time.monotonic() < deadline:
            if not self._is_alive(pid):
                return
            time.sleep(0.1)

        if self._is_alive(pid):
            log.warning(
                "pid=%d (%r) did not stop in %.1fs — sending SIGKILL", pid, name, _GRACEFUL_TIMEOUT
            )
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


# Module-level singleton used by views and AppConfig.
process_manager = ProcessManager()
