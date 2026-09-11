import threading
from .codex_usage import RolloutReader
from .telemetry import LOG, Store


class Collector:
    def __init__(self, config, backfill=False):
        self.config = config
        self.store = Store(config.data_dir)
        self.reader = RolloutReader(config, self.store, backfill)
        self.stop_event = threading.Event()
        self.receiver = None
        self.thread = None

    def start(self):
        if self.config.otel_port:
            from .otel import make_receiver
            try:
                self.receiver = make_receiver(self.store, self.config.otel_port)
            except OSError:
                LOG.warning("otel_receiver_unavailable port=%d; rollout fallback remains active", self.config.otel_port)
            if self.receiver:
                threading.Thread(target=self.receiver.serve_forever, daemon=True).start()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        LOG.info("collector_started metadata_only=true")
        while not self.stop_event.is_set():
            try:
                self.reader.poll()
            except Exception:
                LOG.warning("collector_poll_failed; retrying next interval")
            self.stop_event.wait(self.config.poll_seconds)

    def close(self):
        self.stop_event.set()
        if self.receiver:
            self.receiver.shutdown()
            self.receiver.server_close()
        if self.thread:
            self.thread.join(timeout=5)
