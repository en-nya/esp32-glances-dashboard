try:
    import ujson as json
except ImportError:
    import json

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
            "cpu_percent": self._get_value("/api/3/cpu/total"),
            "mem_percent": self._get_value("/api/3/mem/percent"),
            "disk_percent": self._get_disk_percent(),
        }

    def _get_value(self, path):
        data = self._get_json(path)
        if isinstance(data, dict):
            value = data.get("value")
            if value is None and len(data) == 1:
                value = list(data.values())[0]
            return value
        return data

    def _get_disk_percent(self):
        data = self._get_json("/api/3/fs")
        if isinstance(data, list):
            for item in data:
                if item.get("mnt_point") == "/":
                    return item.get("percent")
            if data:
                return data[0].get("percent")
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
