import time
from collections import defaultdict

class MetricsRegistry:
    def __init__(self):
        self._counters = defaultdict(int)
        self._gauges = defaultdict(float)
        self._histograms = defaultdict(list)

    def counter_inc(self, name: str, labels: dict = None, value: int = 1):
        key = self._label_key(name, labels)
        self._counters[key] += value

    def gauge_set(self, name: str, value: float, labels: dict = None):
        key = self._label_key(name, labels)
        self._gauges[key] = value

    def gauge_inc(self, name: str, labels: dict = None):
        key = self._label_key(name, labels)
        self._gauges[key] += 1

    def gauge_dec(self, name: str, labels: dict = None):
        key = self._label_key(name, labels)
        self._gauges[key] -= 1

    def observe(self, name: str, value: float, labels: dict = None):
        key = self._label_key(name, labels)
        self._histograms[key].append(value)

    def render(self) -> str:
        lines = ["# HELP wfgy metrics", "# TYPE wfgy metrics"]
        buckets = [0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0]
        seen_help = set()

        for key, count in sorted(self._counters.items()):
            name, label_str = self._parse_key(key)
            if name not in seen_help:
                lines.insert(0, f"# HELP {name} Total counter")
                lines.insert(1, f"# TYPE {name} counter")
                seen_help.add(name)
            lines.append(f"{name}{{{label_str}}} {count}")

        for key, val in sorted(self._gauges.items()):
            name, label_str = self._parse_key(key)
            if name not in seen_help:
                seen_help.add(name)
            lines.append(f"{name}{{{label_str}}} {val}")

        for key, vals in sorted(self._histograms.items()):
            name, label_str = self._parse_key(key)
            base_name = name.replace("_bucket", "").replace("_count", "").replace("_sum", "")
            if base_name not in seen_help:
                lines.insert(0, f"# HELP {base_name} Histogram")
                lines.insert(1, f"# TYPE {base_name} histogram")
                seen_help.add(base_name)
            n = len(vals)
            total = sum(vals)
            lines.append(f"{base_name}_sum{{{label_str}}} {total}")
            lines.append(f"{base_name}_count{{{label_str}}} {n}")
            for b in buckets:
                le = sum(1 for v in vals if v <= b)
                lines.append(f"{base_name}_bucket{{{label_str},le=\"{b}\"}} {le}")
            lines.append(f"{base_name}_bucket{{{label_str},le=\"+Inf\"}} {n}")

        return "\n".join(lines) + "\n"

    @staticmethod
    def _label_key(name, labels):
        if not labels:
            return f"{name}|"
        parts = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}|{parts}"

    @staticmethod
    def _parse_key(key):
        name, _, label_part = key.partition("|")
        return name, label_part

METRICS = MetricsRegistry()
