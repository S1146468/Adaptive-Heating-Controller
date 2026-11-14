"""Validate this release's deliberately minimal, privilege-free metadata contract."""

import argparse
from pathlib import Path

import jsonschema
import yaml


URL = "https://github.com/S1146468/Adaptive-Heating-Controller"
APP_PROPERTIES = {
    "name": {"const": "Adaptive Heating Controller"},
    "version": {"const": "0.1.0"},
    "slug": {"const": "adaptive_heating_controller"},
    "description": {"type": "string", "minLength": 1},
    "url": {"const": URL},
    "arch": {"const": ["aarch64"]},
    "startup": {"const": "application"},
    "boot": {"const": "manual"},
    "stage": {"const": "experimental"},
    "init": {"const": True},
    "timeout": {"const": 10},
    "options": {"const": {}},
    "schema": {"const": {}},
}
REPO_PROPERTIES = {
    "name": {"type": "string", "minLength": 1},
    "url": {"const": URL},
    "maintainer": {"type": "string", "minLength": 1},
}


def validate(root: Path) -> None:
    for path, properties in (
        ("repository.yaml", REPO_PROPERTIES),
        ("adaptive_heating_controller/config.yaml", APP_PROPERTIES),
    ):
        jsonschema.validate(
            yaml.safe_load((root / path).read_text()),
            {
                "type": "object",
                "properties": properties,
                "required": list(properties),
                "additionalProperties": False,
            },
        )
    # This narrow allowlist rejects permissions/options as well as malformed metadata.
    version = (root / "adaptive_heating_controller/app/__init__.py").read_text()
    if '__version__ = "0.1.0"' not in version:
        raise ValueError("Package version must match the manifest")
    for path in ("Dockerfile", "run.sh", "app/__main__.py"):
        if not (root / "adaptive_heating_controller" / path).is_file():
            raise ValueError(f"Missing app file: {path}")
    print("Repository and app metadata valid (ARM64, read-only, no privileges)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path("."))
    validate(parser.parse_args().root)
