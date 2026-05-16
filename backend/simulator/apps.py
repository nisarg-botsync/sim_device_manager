import atexit
import logging
import os

from django.apps import AppConfig

log = logging.getLogger(__name__)


class SimulatorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "simulator"

    def ready(self) -> None:
        from .process_manager import process_manager

        # Register cleanup so all subprocesses die when Django exits.
        atexit.register(process_manager.shutdown_all)

        # Reconcile stale "running" devices left by a previous server instance.
        # Skip when running under pytest — Django initialises apps before the first
        # test runs, so the DB is accessible but we don't want side-effects.
        import sys

        if "pytest" in sys.modules:
            return

        try:
            process_manager.reconcile_on_startup()
        except Exception:
            # DB might not be set up yet (e.g. first-run before migrations).
            log.debug("Could not reconcile simulators on startup", exc_info=True)
