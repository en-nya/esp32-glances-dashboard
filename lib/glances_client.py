# SPDX-License-Identifier: AGPL-3.0-or-later
try:
    import urequests as requests
except ImportError:
    requests = None

from config import GLANCES_BASE_URL, HTTP_TIMEOUT_SECONDS


class GlancesClient:
    def __init__(self, base_url=GLANCES_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.status = {}
        self.changed = True
        self.tasks = (
            {"name": "quicklook", "path": "/api/4/quicklook", "interval": 500, "next": 0, "handler": self._apply_quicklook},
            {"name": "containers", "path": "/api/4/containers", "interval": 5000, "next": 0, "handler": self._apply_containers},
            {"name": "network", "path": "/api/4/network", "interval": 1000, "next": 0, "handler": self._apply_network},
            {"name": "load", "path": "/api/4/load", "interval": 5000, "next": 0, "handler": self._apply_load},
            {"name": "sensors", "path": "/api/4/sensors", "interval": 5000, "next": 0, "handler": self._apply_sensors},
            {"name": "uptime", "path": "/api/4/uptime", "interval": 5000, "next": 0, "handler": self._apply_uptime},
            {"name": "fs", "path": "/api/4/fs", "interval": 15000, "next": 0, "handler": self._apply_fs},
        )
        self.task_index = 0

    def poll(self, now):
        self.changed = False
        selected = None
        selected_index = None
        task_count = len(self.tasks)
        for offset in range(task_count):
            index = (self.task_index + offset) % task_count
            task = self.tasks[index]
            if now >= task["next"] and (selected is None or task["next"] < selected["next"]):
                selected = task
                selected_index = index

        if selected is None:
            return False

        self.task_index = (selected_index + 1) % task_count
        selected["next"] = now + selected["interval"]
        data = self._get_json(selected["path"], None)
        if data is not None:
            selected["handler"](data)
        return self.changed

    def snapshot(self):
        return self.status

    def _set(self, key, value):
        if self.status.get(key) != value:
            self.status[key] = value
            self.changed = True

    def _apply_quicklook(self, data):
        if not isinstance(data, dict):
            return
        self._set("cpu_percent", data.get("cpu"))
        self._set("mem_percent", data.get("mem"))

    def _apply_network(self, items):
        self._set("net_rx_rate", self._network_rate(items, "bytes_recv_rate_per_sec"))
        self._set("net_tx_rate", self._network_rate(items, "bytes_sent_rate_per_sec"))

    def _apply_sensors(self, sensors):
        self._set("temperature", self._temperature(sensors))

    def _apply_load(self, load):
        if not isinstance(load, dict):
            return
        self._set("load", (load.get("min1"), load.get("min5"), load.get("min15")))

    def _apply_uptime(self, uptime):
        self._set("uptime", uptime)

    def _apply_fs(self, fs_items):
        disk = self._disk(fs_items)
        self._set("disk_percent", disk.get("percent"))
        self._set("disk_used", disk.get("used"))
        self._set("disk_size", disk.get("size"))

    def _apply_containers(self, containers):
        docker = self._docker(containers)
        self._set("docker_total", docker.get("total", 0))
        self._set("docker_running", docker.get("running", 0))

    def _disk(self, fs_items):
        if not isinstance(fs_items, list):
            return {}
        for item in fs_items:
            if item.get("mnt_point") in ("/", "/rootfs"):
                return item
        if fs_items:
            return fs_items[0]
        return {}

    def _network_rate(self, items, key):
        if not isinstance(items, list):
            return None
        total = 0
        found = False
        for item in items:
            name = item.get("interface_name", "")
            if name == "lo":
                continue
            value = item.get(key)
            if value is not None:
                total += value
                found = True
        return total if found else None

    def _temperature(self, sensors):
        if not isinstance(sensors, list):
            return None
        temps = []
        for item in sensors:
            if item.get("unit") == "C" or "temperature" in str(item.get("type", "")):
                value = item.get("value")
                if value is not None:
                    temps.append(value)
        if not temps:
            return None
        return max(temps)

    def _docker(self, containers):
        if not isinstance(containers, list):
            return {}
        running = 0
        for item in containers:
            status = str(item.get("status", item.get("State", item.get("state", "")))).lower()
            if "running" in status or "healthy" in status or status == "true":
                running += 1
        return {"total": len(containers), "running": running}

    def _get_json(self, path, default):
        if requests is None:
            raise RuntimeError("urequests module is not available")

        timeout = HTTP_TIMEOUT_SECONDS
        if path in ("/api/4/containers", "/api/4/fs"):
            timeout = max(HTTP_TIMEOUT_SECONDS, 4)

        response = None
        try:
            response = requests.get(
                self.base_url + path,
                timeout=timeout,
            )
            if getattr(response, "status_code", 200) >= 400:
                return default
            return response.json()
        except Exception as exc:
            print("Glances endpoint skipped", path, exc)
            return default
        finally:
            if response:
                response.close()
