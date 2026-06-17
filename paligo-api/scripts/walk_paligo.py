#!/usr/bin/env python3
"""Walk the Paligo folder/document tree and save an inventory snapshot.

Enumerates every folder and document (metadata only — list views return empty
`content`) so you can refer to a local inventory instead of re-walking the API
each time. Paced to respect the read rate limit, and fault-tolerant: a folder
that 404s is recorded and skipped rather than aborting the whole walk.

Credentials (resolved in this order):
  1. Environment variables PALIGO_INSTANCE, PALIGO_USERNAME, PALIGO_API_KEY
  2. A .env file (KEY=VALUE lines) given via --env, else the first .env found
     walking up from the current directory.

Outputs (to --out, default ./paligo-inventory/):
  paligo-tree.json       hierarchical folders -> documents
  paligo-documents.json  flat list of doc stubs, each with its folder path
  paligo-inventory.txt   human-readable indented outline
  paligo-manifest.json   run metadata (counts, skipped folders, timestamp-free)

Key instance behaviors this script handles (see the skill's endpoints.md):
  - A folder's `children` MIXES subfolders and documents; recurse only
    `type == "folder"` (GET /folders/{id} on a document id returns 404).
  - Documents per folder come from GET /documents?parent= (paginated; includes
    publications as well as components).
  - Pagination result arrays are keyed by resource name, and `next_page` is the
    empty string "" on the last page.

Usage:
  python3 walk_paligo.py                       # creds from env or discovered .env
  python3 walk_paligo.py --env /path/to/.env --out ./data
  python3 walk_paligo.py --pace 1.3            # seconds between requests
"""
import argparse, base64, json, os, sys, time, urllib.request, urllib.error
from pathlib import Path
from urllib.parse import urlencode


def find_env(explicit=None):
    if explicit:
        return Path(explicit)
    for d in [Path.cwd(), *Path.cwd().parents]:
        cand = d / ".env"
        if cand.is_file():
            return cand
    return None


def load_creds(env_path):
    vals = {}
    if env_path and env_path.is_file():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip()
    # environment overrides file
    for k in ("PALIGO_INSTANCE", "PALIGO_USERNAME", "PALIGO_API_KEY"):
        if os.environ.get(k):
            vals[k] = os.environ[k]
    missing = [k for k in ("PALIGO_INSTANCE", "PALIGO_USERNAME", "PALIGO_API_KEY")
               if not vals.get(k)]
    if missing:
        sys.exit(f"Missing credentials: {', '.join(missing)} "
                 f"(set env vars or provide a .env via --env)")
    return vals


class Client:
    def __init__(self, instance, username, api_key, pace):
        self.base = f"https://{instance}.paligoapp.com/api/v2"
        self.auth = "Basic " + base64.b64encode(
            f"{username}:{api_key}".encode()).decode()
        self.pace = pace
        self.calls = 0

    def get(self, path, params=None):
        url = self.base + path + ("?" + urlencode(params) if params else "")
        for _ in range(5):
            time.sleep(self.pace)
            req = urllib.request.Request(
                url, headers={"Authorization": self.auth, "Accept": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    self.calls += 1
                    return json.loads(r.read().decode())
            except urllib.error.HTTPError as ex:
                if ex.code == 429:
                    wait = int(ex.headers.get("Retry-After", "30"))
                    print(f"  429 rate-limited; sleeping {wait}s", file=sys.stderr)
                    time.sleep(wait)
                    continue
                raise
        raise RuntimeError(f"giving up on {url} after retries")

    def paginate(self, path, params=None, per_page=100):
        params = dict(params or {}, page=1, per_page=per_page)
        while True:
            data = self.get(path, params)
            # result array is keyed by resource name, not a generic key
            items = next((v for v in data.values() if isinstance(v, list)), [])
            yield from items
            if data.get("next_page", "") == "" or params["page"] >= data.get("total_pages", 1):
                break
            params["page"] += 1


DOC_FIELDS = ("id", "name", "uuid", "type", "release_status", "checkout",
              "languages", "created_at", "modified_at", "parent_resource")


def doc_stub(d):
    return {k: d.get(k) for k in DOC_FIELDS}


def walk_folder(cli, folder_id, name, path, errors):
    try:
        folder = cli.get(f"/folders/{folder_id}")
    except urllib.error.HTTPError as ex:
        errors.append({"folder_id": folder_id, "path": path,
                       "error": f"GET /folders/{folder_id} -> {ex.code}"})
        print(f"  !! skip [{folder_id}] {path}  (HTTP {ex.code})", file=sys.stderr)
        return {"id": folder_id, "name": name, "path": path, "type": "folder",
                "documents": [], "folders": [], "error": ex.code}
    docs = [doc_stub(d) for d in cli.paginate("/documents", {"parent": folder_id})]
    children = []
    # children mixes folders + documents; recurse folders only.
    for child in folder.get("children", []):
        if child.get("type") != "folder":
            continue
        cid = child["id"]
        cname = child.get("name", str(cid))
        children.append(walk_folder(cli, cid, cname, f"{path}/{cname}", errors))
    print(f"  {path}  ({len(docs)} docs, {len(children)} subfolders)", file=sys.stderr)
    return {"id": folder_id, "name": name, "path": path, "type": "folder",
            "documents": docs, "folders": children}


def main():
    ap = argparse.ArgumentParser(description="Walk the Paligo tree and save an inventory.")
    ap.add_argument("--env", help="path to a .env file with PALIGO_* creds")
    ap.add_argument("--out", default="paligo-inventory", help="output directory")
    ap.add_argument("--pace", type=float, default=1.3,
                    help="seconds between requests (default 1.3 ~= 46/min, under the 50/min read cap)")
    args = ap.parse_args()

    creds = load_creds(find_env(args.env))
    cli = Client(creds["PALIGO_INSTANCE"], creds["PALIGO_USERNAME"],
                 creds["PALIGO_API_KEY"], args.pace)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    print(f"Walking {cli.base} ...", file=sys.stderr)
    errors = []
    tree = []
    for r in cli.paginate("/folders"):
        rid, rname = r["id"], r.get("name", str(r["id"]))
        tree.append(walk_folder(cli, rid, rname, f"/{rname}", errors))

    flat = []
    def collect(node):
        for d in node["documents"]:
            flat.append({**d, "folder_path": node["path"], "folder_id": node["id"]})
        for c in node["folders"]:
            collect(c)
    for n in tree:
        collect(n)

    def count_folders(nodes):
        return sum(1 + count_folders(n["folders"]) for n in nodes)

    manifest = {
        "instance": creds["PALIGO_INSTANCE"],
        "base_url": cli.base,
        "root_folders": len(tree),
        "total_folders": count_folders(tree),
        "total_documents": len(flat),
        "api_calls": cli.calls,
        "skipped_folders": errors,
    }

    (out / "paligo-tree.json").write_text(json.dumps(tree, indent=2))
    (out / "paligo-documents.json").write_text(json.dumps(flat, indent=2))
    (out / "paligo-manifest.json").write_text(json.dumps(manifest, indent=2))

    lines = []
    def render(node, depth):
        lines.append("  " * depth + f"[{node['id']}] {node['name']}/")
        for d in node["documents"]:
            lines.append("  " * (depth + 1)
                         + f"- ({d['id']}) {d['name']}  [{d.get('release_status', '')}]")
        for c in node["folders"]:
            render(c, depth + 1)
    for n in tree:
        render(n, 0)
    (out / "paligo-inventory.txt").write_text("\n".join(lines) + "\n")

    print("\n=== DONE ===", file=sys.stderr)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
