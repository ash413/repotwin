"""Parses infrastructure/config files to detect declared services and dependencies."""

import os
import re
from dataclasses import dataclass, field
from typing import List, Dict

try:
    import yaml
except ImportError:
    yaml = None

# image name substring -> (node_id, node_type, label)
KNOWN_IMAGES = {
    "postgres": ("postgres", "database", "PostgreSQL"),
    "redis": ("redis", "cache", "Redis"),
    "mongo": ("mongodb", "database", "MongoDB"),
    "mysql": ("mysql", "database", "MySQL"),
    "rabbitmq": ("rabbitmq", "queue", "RabbitMQ"),
    "kafka": ("kafka", "queue", "Kafka"),
    "elasticsearch": ("elasticsearch", "database", "Elasticsearch"),
}

# pip package -> (node_id, node_type, label) for external integrations not covered by containers
KNOWN_PACKAGES = {
    "stripe": ("stripe", "external_api", "Stripe"),
    "celery": ("celery", "queue", "Celery"),
    "boto3": ("aws", "external_api", "AWS"),
    "sendgrid": ("sendgrid", "external_api", "SendGrid"),
    "twilio": ("twilio", "external_api", "Twilio"),
}


@dataclass
class ConfigAnalysis:
    compose_services: List[Dict] = field(default_factory=list)  # {name, image, node_id, node_type, label, file}
    packages: List[Dict] = field(default_factory=list)  # {name, node_id, node_type, label, file}
    env_vars: List[Dict] = field(default_factory=list)  # {name, file, line}


def _parse_compose(root: str, rel_path: str) -> List[Dict]:
    if yaml is None:
        return []
    full_path = os.path.join(root, rel_path)
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            data = yaml.safe_load(f)
    except Exception:
        return []

    services = []
    if not data or "services" not in data:
        return services

    for svc_name, svc_def in (data.get("services") or {}).items():
        image = (svc_def or {}).get("image", "") or ""
        matched = None
        for substr, info in KNOWN_IMAGES.items():
            if substr in image.lower() or substr in svc_name.lower():
                matched = info
                break
        node_id, node_type, label = matched or (svc_name, "service", svc_name)
        services.append({
            "name": svc_name,
            "image": image,
            "node_id": node_id,
            "node_type": node_type,
            "label": label,
            "file": rel_path,
        })
    return services


def _parse_requirements(root: str, rel_path: str) -> List[Dict]:
    full_path = os.path.join(root, rel_path)
    packages = []
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                pkg_name = re.split(r"[<>=\[; ]", line)[0].lower()
                if pkg_name in KNOWN_PACKAGES:
                    node_id, node_type, label = KNOWN_PACKAGES[pkg_name]
                    packages.append({
                        "name": pkg_name,
                        "node_id": node_id,
                        "node_type": node_type,
                        "label": label,
                        "file": rel_path,
                    })
    except Exception:
        pass
    return packages


def _parse_env_file(root: str, rel_path: str) -> List[Dict]:
    full_path = os.path.join(root, rel_path)
    env_vars = []
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            for i, raw_line in enumerate(f, start=1):
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name = line.split("=", 1)[0].strip()
                env_vars.append({"name": name, "file": rel_path, "line": i})
    except Exception:
        pass
    return env_vars


def analyze_configs(root: str, config_files: List[str]) -> ConfigAnalysis:
    result = ConfigAnalysis()
    for rel_path in config_files:
        fname = os.path.basename(rel_path)
        if fname.startswith("docker-compose"):
            result.compose_services.extend(_parse_compose(root, rel_path))
        elif fname == "requirements.txt":
            result.packages.extend(_parse_requirements(root, rel_path))
        elif fname.startswith(".env"):
            result.env_vars.extend(_parse_env_file(root, rel_path))
    return result
