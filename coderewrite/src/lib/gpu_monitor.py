# File: gpu_monitor.py
# Description: Tracks GPU VRAM and power usage across pipeline phases using pynvml.
# Author: Adam Zvara (xzvara01)
# Date: 03/2026


import threading
import time

try:
    import pynvml

    _PYNVML_AVAILABLE = True
except ImportError:
    _PYNVML_AVAILABLE = False

# Reference-counted NVML lifecycle: nvmlInit is called once on first use and
# nvmlShutdown is called when the last active monitor exits.
_nvml_lock = threading.Lock()
_nvml_refcount = 0


def _nvml_acquire() -> None:
    global _nvml_refcount
    with _nvml_lock:
        if _nvml_refcount == 0:
            pynvml.nvmlInit()
        _nvml_refcount += 1


def _nvml_release() -> None:
    global _nvml_refcount
    with _nvml_lock:
        _nvml_refcount -= 1
        if _nvml_refcount == 0:
            pynvml.nvmlShutdown()


class GPUMonitor:
    """Context manager that samples GPU VRAM and power usage at a fixed interval.

    Usage::

        with GPUMonitor(gpu_index=0) as monitor:
            run_phase()
        print(monitor.summary())

    When ``pynvml`` is not installed the monitor is a no-op and ``summary()``
    returns an empty dict.
    """

    def __init__(self, gpu_index: int = 0, interval: float = 0.5):
        self._available = _PYNVML_AVAILABLE
        self._gpu_index = gpu_index
        self.interval = interval
        self.samples: list[dict] = []
        self.running = False

    def _sample(self) -> None:
        while self.running:
            mem = pynvml.nvmlDeviceGetMemoryInfo(self._handle)
            power = pynvml.nvmlDeviceGetPowerUsage(self._handle)  # mW
            self.samples.append(
                {
                    "vram_used_gb": mem.used / 1e9,
                    "power_w": power / 1000,
                    "timestamp": time.time(),
                }
            )
            time.sleep(self.interval)

    def __enter__(self) -> "GPUMonitor":
        if self._available:
            _nvml_acquire()
            self._handle = pynvml.nvmlDeviceGetHandleByIndex(self._gpu_index)
            self.running = True
            self._thread = threading.Thread(target=self._sample, daemon=True)
            self._thread.start()
        return self

    def __exit__(self, *args) -> None:
        if self._available:
            self.running = False
            self._thread.join()
            _nvml_release()

    def summary(self) -> dict:
        """Return aggregated metrics for the monitored period.

        Keys:
            peak_vram_gb  — maximum observed VRAM usage in GB
            avg_power_w   — mean power draw in Watts
            duration_s    — wall-clock duration of the monitored phase
            energy_kwh    — estimated energy consumed in kWh
        """
        if not self.samples:
            return {}
        powers = [s["power_w"] for s in self.samples]
        vrams = [s["vram_used_gb"] for s in self.samples]
        duration = self.samples[-1]["timestamp"] - self.samples[0]["timestamp"]
        avg_power = sum(powers) / len(powers)
        energy_kwh = avg_power * duration / 3600 / 1000
        return {
            "peak_vram_gb": max(vrams),
            "avg_power_w": avg_power,
            "duration_s": duration,
            "energy_kwh": energy_kwh,
        }
