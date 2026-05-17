try:
    import urequests as requests
except ImportError:
    requests = None

from config import GLANCES_BASE_URL, HTTP_TIMEOUT_SECONDS


class GlancesClient:
    def __init__(self, base_url=GLANCES_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def fetch_summary(self):
        return {
            "cpu_percent": self._cpu_percent(),
            "mem_percent": self._mem_percent(),
            "disk_percent": self._disk_percent(),
        }

    def _cpu_percent(self):
        cpu = self._get_json("/api/4/cpu")
        total = cpu.get("total")
        if total is not None:
            return total

        idle = cpu.get("idle")
        if idle is not None:
            return max(0, 100 - idle)

        return None

    def _mem_percent(self):
        return self._get_json("/api/4/mem").get("percent")

    def _disk_percent(self):
        fs_items = self._get_json("/api/4/fs")
        for item in fs_items:
            if item.get("mnt_point") in ("/", "/rootfs"):
                return item.get("percent")
        if fs_items:
            return fs_items[0].get("percent")
        return None

    def _get_json(self, path):
        if requests is None:
            raise RuntimeError("urequests module is not available")

        response = requests.get(
            self.base_url + path,
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        try:
            return response.json()
        finally:
            response.close()
