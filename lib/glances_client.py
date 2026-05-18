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
        self.uptime_base = None
        self.uptime_base_ticks = None
        self._network_total_updated = True
        self._network_total_next = 0
        self._time_base = None
        self._time_base_ticks = None
        self._time_next = 0
        self.tasks = (
            {"name": "quicklook", "path": "/api/4/quicklook", "interval": 1000, "next": 0, "handler": self._apply_quicklook},
            {"name": "containers", "path": "/api/4/containers", "interval": 600000, "next": 0, "handler": self._apply_docker},
            {"name": "network", "path": "/api/4/network", "interval": 5000, "next": 0, "handler": self._apply_network},
            {"name": "load", "path": "/api/4/load", "interval": 5000, "next": 0, "handler": self._apply_load},
            {"name": "sensors", "path": "/api/4/sensors", "interval": 5000, "next": 0, "handler": self._apply_sensors},
            {"name": "uptime", "path": "/api/4/uptime", "interval": 300000, "next": 0, "handler": self._apply_uptime},
            {"name": "fs", "path": "/api/4/fs", "interval": 600000, "next": 0, "handler": self._apply_fs},
        )
        self.task_index = 0

    def poll(self, now):
        self.changed = False

        if now >= self._network_total_next:
            self._network_total_updated = True
            self._network_total_next = now + 1800000

        if now >= self._time_next:
            self._sync_time()
            self._time_next = now + 300000

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
        result = self.status.copy()
        if self.uptime_base and self.uptime_base_ticks:
            result['uptime'] = self._get_current_uptime()
        current_time = self._get_current_time()
        if current_time:
            result['current_time'] = current_time
        return result

    def _get_current_uptime(self):
        import time
        if not self.uptime_base or not self.uptime_base_ticks:
            return self.status.get('uptime')

        elapsed_ms = time.ticks_diff(time.ticks_ms(), self.uptime_base_ticks)
        elapsed_sec = elapsed_ms // 1000

        base_str = str(self.uptime_base)
        if 'day' in base_str:
            parts = base_str.split(',')
            day_part = parts[0].strip()
            days = int(day_part.split()[0])
            time_part = parts[1].strip() if len(parts) > 1 else '0:00:00'
        else:
            days = 0
            time_part = base_str

        time_parts = time_part.split(':')
        hours = int(time_parts[0]) if len(time_parts) > 0 else 0
        minutes = int(time_parts[1]) if len(time_parts) > 1 else 0
        seconds = int(time_parts[2]) if len(time_parts) > 2 else 0

        total_seconds = days * 86400 + hours * 3600 + minutes * 60 + seconds + elapsed_sec

        new_days = total_seconds // 86400
        remaining = total_seconds % 86400
        new_hours = remaining // 3600
        remaining = remaining % 3600
        new_minutes = remaining // 60
        new_seconds = remaining % 60

        if new_days > 0:
            return '{} day, {}:{:02d}:{:02d}'.format(new_days, new_hours, new_minutes, new_seconds)
        else:
            return '{}:{:02d}:{:02d}'.format(new_hours, new_minutes, new_seconds)

    def _sync_time(self):
        import time
        data = self._get_json("/api/4/now", None)
        if data and isinstance(data, dict):
            iso_time = data.get('iso', '')
            if iso_time:
                self._time_base = iso_time
                self._time_base_ticks = time.ticks_ms()
                print("Time synced:", iso_time)

    def _get_current_time(self):
        import time
        if not self._time_base or not self._time_base_ticks:
            return None

        elapsed_ms = time.ticks_diff(time.ticks_ms(), self._time_base_ticks)
        elapsed_sec = elapsed_ms // 1000

        iso_str = self._time_base
        if 'T' not in iso_str:
            return None

        date_part = iso_str.split('T')[0]
        time_part = iso_str.split('T')[1]
        time_str = time_part.split('+')[0].split('-')[0]

        date_parts = date_part.split('-')
        if len(date_parts) < 3:
            return None

        year = int(date_parts[0])
        month = int(date_parts[1])
        day = int(date_parts[2])

        time_parts = time_str.split(':')
        if len(time_parts) < 3:
            return None

        hours = int(time_parts[0])
        minutes = int(time_parts[1])
        seconds = int(time_parts[2].split('.')[0])

        total_seconds = hours * 3600 + minutes * 60 + seconds + elapsed_sec + 28800
        day_offset = total_seconds // 86400
        total_seconds = total_seconds % 86400

        new_hours = total_seconds // 3600
        remaining = total_seconds % 3600
        new_minutes = remaining // 60
        new_seconds = remaining % 60

        if day_offset > 0:
            day += day_offset
            days_in_month = [31, 29 if year % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            if day > days_in_month[month - 1]:
                day = 1
                month += 1
                if month > 12:
                    month = 1
                    year += 1

        return '{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'.format(year, month, day, new_hours, new_minutes, new_seconds)

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
        if not hasattr(self, '_network_total_updated') or self._network_total_updated:
            self._set("net_rx_total", self._network_total(items, "bytes_recv_gauge"))
            self._set("net_tx_total", self._network_total(items, "bytes_sent_gauge"))
            self._network_total_updated = False

    def _apply_sensors(self, sensors):
        self._set("temperature", self._temperature(sensors))

    def _apply_load(self, load):
        if not isinstance(load, dict):
            return
        self._set("load", (load.get("min1"), load.get("min5"), load.get("min15")))

    def _apply_uptime(self, uptime):
        import time
        self.uptime_base = uptime
        self.uptime_base_ticks = time.ticks_ms()
        self._set("uptime", uptime)

    def _apply_fs(self, fs_items):
        disk = self._disk(fs_items)
        self._set("disk_percent", disk.get("percent"))
        self._set("disk_used", disk.get("used"))
        self._set("disk_size", disk.get("size"))

    def _apply_docker(self, data):
        if isinstance(data, dict):
            containers = data.get("containers", [])
        elif isinstance(data, list):
            containers = data
        else:
            containers = []
        docker = self._parse_docker(containers)
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

    def _network_total(self, items, key):
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

    def _parse_docker(self, containers):
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

        timeout = 1
        if path == "/api/4/docker" or path == "/api/4/containers":
            timeout = 5
        elif path == "/api/4/fs":
            timeout = 3

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
