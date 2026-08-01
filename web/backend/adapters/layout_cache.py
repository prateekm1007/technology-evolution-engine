"""Deterministic clustered layout, cached to disk (scaling tier 1)."""
import json, math, pathlib, hashlib


def compute_layout(gm, cache_dir):
    key = hashlib.sha256(json.dumps([gm.source, len(gm.nodes), len(gm.edges)]).encode()).hexdigest()[:12]
    cache_dir = pathlib.Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / f"layout_{key}.json"
    if cache.exists() and cache.is_file():
        return json.loads(cache.read_text())
    domains = sorted({n["domain"] for n in gm.nodes})
    centers = {d: (math.cos(i / len(domains) * 2 * math.pi), math.sin(i / len(domains) * 2 * math.pi))
               for i, d in enumerate(domains)}
    pos = {}
    for n in gm.nodes:
        cx, cy = centers.get(n["domain"], (0, 0))
        h = int(hashlib.sha256(n["id"].encode()).hexdigest()[:8], 16)
        r, th = (h % 1000) / 1000 * 0.35, ((h >> 10) % 1000) / 1000 * 2 * math.pi
        pos[n["id"]] = [round(cx + r * math.cos(th), 4), round(cy + r * math.sin(th), 4)]
    out = {"positions": pos, "source": gm.source, "key": key}
    cache.write_text(json.dumps(out))
    return out
