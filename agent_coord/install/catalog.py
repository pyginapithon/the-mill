"""Office catalog: book engines, httpds, cloud providers.

Wired = this mill can write a working config today.
Others are allowed (open source or paid) and get a runbook; the mill
book client is MySQL-protocol in v0.1 (MySQL and MariaDB).
Cloud is the same server install on a VM the operator chooses (public Wall/443; MySQL private). mill install cloud = wording + local probes; never cloud API calls.
"""

from __future__ import annotations

from typing import Any

# Mill CLI talks MySQL protocol today. MariaDB is the same wire.
BOOKS: dict[str, dict[str, Any]] = {
    "mysql": {"wired": True, "port": 3306, "license": "open", "note": "v0.1 default"},
    "mariadb": {"wired": True, "port": 3306, "license": "open", "note": "MySQL protocol"},
    "postgres": {"wired": False, "port": 5432, "license": "open", "note": "leftover mill connector"},
    "sqlserver": {"wired": False, "port": 1433, "license": "paid", "note": "leftover mill connector"},
    "oracle": {"wired": False, "port": 1521, "license": "paid", "note": "leftover mill connector"},
}

# Public wall. Mill API stays localhost HTTP behind the httpd.
HTTPDS: dict[str, dict[str, Any]] = {
    "nginx": {"wired": True, "license": "open", "note": "0.4 default TLS edge; FastAPI mill-wall behind it"},
    "caddy": {"wired": False, "license": "open", "note": "leftover vhost snippet"},
    "iis": {"wired": False, "license": "paid", "note": "Windows Server; leftover ARR proxy"},
    "litespeed": {"wired": False, "license": "paid", "note": "leftover vhost snippet"},
    "service": {"wired": True, "license": "open", "note": "dogfood mill process as httpd"},
}

# Same host install on a VM. Printed runbook first-class: aws|azure|gcp|self.
# Other ids remain for normalize aliases only; we do not call provider APIs.
CLOUDS: dict[str, dict[str, Any]] = {
    "aws": {"kind": "hyperscale", "net": "VPC", "fw": "security group", "db": "RDS", "lb": "ALB"},
    "azure": {"kind": "hyperscale", "net": "VNet", "fw": "NSG", "db": "Azure Database", "lb": "App Gateway"},
    "gcp": {"kind": "hyperscale", "net": "VPC", "fw": "VPC firewall", "db": "Cloud SQL", "lb": "GCLB"},
    "oracle": {"kind": "hyperscale", "net": "VCN", "fw": "security list", "db": "Autonomous/DB system", "lb": "flexible LB"},
    "ibm": {"kind": "hyperscale", "net": "VPC", "fw": "security group", "db": "Databases for PostgreSQL/MySQL", "lb": "load balancer"},
    "alibaba": {"kind": "hyperscale", "net": "VPC", "fw": "security group", "db": "ApsaraDB", "lb": "SLB"},
    "tencent": {"kind": "hyperscale", "net": "VPC", "fw": "security group", "db": "TencentDB", "lb": "CLB"},
    "huawei": {"kind": "hyperscale", "net": "VPC", "fw": "security group", "db": "RDS", "lb": "ELB"},
    "lightsail": {"kind": "vps", "net": "VPC", "fw": "firewall", "db": "Lightsail DB", "lb": "Lightsail LB"},
    "digitalocean": {"kind": "vps", "net": "VPC", "fw": "cloud firewall", "db": "Managed MySQL", "lb": "Load Balancer"},
    "linode": {"kind": "vps", "net": "VPC", "fw": "cloud firewall", "db": "Managed DB", "lb": "NodeBalancer"},
    "akamai": {"kind": "vps", "net": "VPC", "fw": "cloud firewall", "db": "Managed DB", "lb": "NodeBalancer"},
    "vultr": {"kind": "vps", "net": "VPC", "fw": "firewall group", "db": "Managed DB", "lb": "Load Balancer"},
    "hetzner": {"kind": "vps", "net": "private network", "fw": "firewall", "db": "Managed DB", "lb": "Load Balancer"},
    "ovh": {"kind": "vps", "net": "vRack / private", "fw": "firewall", "db": "Public Cloud DB", "lb": "Load Balancer"},
    "scaleway": {"kind": "vps", "net": "Private Network", "fw": "security group", "db": "Managed DB", "lb": "Load Balancer"},
    "upcloud": {"kind": "vps", "net": "SDN", "fw": "firewall", "db": "Managed DB", "lb": "Load Balancer"},
    "civo": {"kind": "vps", "net": "private network", "fw": "firewall", "db": "Managed DB", "lb": "Load Balancer"},
    "exoscale": {"kind": "vps", "net": "private network", "fw": "security group", "db": "DBaaS", "lb": "Network Load Balancer"},
    "kamatera": {"kind": "vps", "net": "private LAN", "fw": "firewall", "db": "self-managed", "lb": "optional"},
    "fly": {"kind": "paas", "net": "6PN / private", "fw": "services bind", "db": "Fly Postgres / self", "lb": "Anycast"},
    "render": {"kind": "paas", "net": "private service", "fw": "service allowlist", "db": "Render MySQL/Postgres", "lb": "platform"},
    "railway": {"kind": "paas", "net": "private network", "fw": "service", "db": "plugin MySQL", "lb": "platform"},
    "self": {"kind": "vps", "net": "private LAN/VPC", "fw": "host firewall", "db": "mysqld on the VM", "lb": "optional"},
}



# First-class printed providers for mill install cloud runbook (not ~24 peers).
PRINTED_CLOUD_IDS: tuple[str, ...] = ("aws", "azure", "gcp", "self")


def printed_cloud_id(name: str) -> str:
    """Map any normalized cloud id to a printed runbook id (aws|azure|gcp|self)."""
    pid = normalize_cloud(name)
    return pid if pid in PRINTED_CLOUD_IDS else "self"


def book_ids() -> list[str]:
    return list(BOOKS)


def httpd_ids() -> list[str]:
    return list(HTTPDS)


def cloud_ids() -> list[str]:
    return list(CLOUDS)


def normalize_book(name: str) -> str:
    raw = (name or "mysql").strip().lower()
    aliases = {"mariadb": "mariadb", "maria": "mariadb", "pg": "postgres", "postgresql": "postgres", "mssql": "sqlserver"}
    raw = aliases.get(raw, raw)
    return raw if raw in BOOKS else "mysql"


def normalize_httpd(name: str) -> str:
    raw = (name or "nginx").strip().lower()
    aliases = {"openlitespeed": "litespeed", "windows": "iis"}
    raw = aliases.get(raw, raw)
    if raw in HTTPDS:
        return raw
    return "nginx"


def normalize_cloud(name: str) -> str:
    raw = (name or "self").strip().lower()
    aliases = {
        "amazon": "aws",
        "amazon web services": "aws",
        "microsoft": "azure",
        "google": "gcp",
        "google cloud": "gcp",
        "oci": "oracle",
        "oracle cloud": "oracle",
        "ibm cloud": "ibm",
        "do": "digitalocean",
        "digital ocean": "digitalocean",
        "akamai linode": "linode",
        "aliyun": "alibaba",
        "ali": "alibaba",
        "qcloud": "tencent",
        "fly.io": "fly",
        "vps": "self",
        "other": "self",
        "any": "self",
    }
    raw = aliases.get(raw, raw)
    return raw if raw in CLOUDS else "self"


def cloud_runbook(provider: str) -> str:
    """Provider appendix for mill install cloud. Deep stubs: aws|azure|gcp; else generic Linux (self)."""
    requested = normalize_cloud(provider)
    pid = printed_cloud_id(requested)
    meta = CLOUDS[pid]
    alias_note = ""
    if requested != pid:
        alias_note = (
            f"Requested provider id `{requested}` is treated as generic Linux VM "
            f"(`self`) in the printed runbook - not a first-class installer.\n\n"
        )
    if pid == "self":
        words = (
            "Provider words here: net=private LAN/VPC (or equivalent), "
            "firewall=host/security-group rules, db=mysqld on the VM, lb=optional."
        )
        fw = "host firewall / security group"
        net = "private network"
    else:
        words = (
            f"Provider words here: net={meta['net']}, firewall={meta['fw']}, "
            f"db={meta['db']} (optional later - OOTB default is mysqld on the VM), "
            f"lb={meta['lb']}."
        )
        fw = meta["fw"]
        net = meta["net"]

    title = {
        "aws": "aws",
        "azure": "azure",
        "gcp": "gcp",
        "self": "generic Linux VM (escape hatch)",
    }[pid]
    playbook = f"docs/install/cloud/{pid}.md"

    return f"""# Cloud office - {title}

{alias_note}Same single-tenant office as a local host: **server** (book + wall) on the VM; desks `mill join` / `mill connect`.
Not multi-tenant SaaS. Not a fourth product.

{words}
Mill does **not** call cloud provider APIs and never stores cloud access keys. Operator (or agent with console access) creates the VM, then on the VM:

```
python -m pip install the-mill
mill install server --apply --public
mill init --yes
```

`--public` = Wall/API reachable off-box. **Never** open MySQL.

## Must
- {fw}: allow **443** for Wall; SSH key auth open only to the operator's current public IP; **3306 not public** / never 0.0.0.0/0 on MySQL.
- Wall HTTPS on **443** with the mill CA (DNS name optional).
- Mill API stays on the host behind TLS; station files stay on desks.
- **Door = invite** on public hosts ([invite requirements](docs/requirements/invite.md)). **No VPN-as-door.**
- Book default: **MySQL 8 (InnoDB)** on the VM, bind `127.0.0.1`. Managed DB later - do not invent migrate.

## Desks / humans
- Desks: `pip install the-mill` -> `mill join --link-file LINKFILE` -> `bash -c 'mill connect DESK >/dev/null 2>&1 & trap "kill $!" EXIT; mill inbox'` ([JOIN.md](docs/JOIN.md)).
- Humans: Wall HTTPS URL only (browser).

## Playbook
Cold-agent steps for this provider: `{playbook}`
(git checkout, or `share/the-mill/{playbook}` in the installed pack).
Read that file before any provider command. Its status line stays `unmeasured` until an end-to-end measure.

## Status
Cloud VM + Linux systemd mill-wall end-to-end: **not measured OOTB** until #502 (`ootb-cloud-aws-azure-gcp`).

## Validate (after measure)
On the VM: `mill install check`. Remote desk: open Wall HTTPS; `mill join` + `mill connect` (do not dump /api/floor into a model).
"""


def cloud_ids_printed() -> list[str]:
    return list(PRINTED_CLOUD_IDS)
