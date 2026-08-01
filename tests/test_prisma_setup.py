import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_prisma_schema_and_config_exist():
    assert (ROOT / "prisma").exists(), "prisma directory is missing"
    assert (ROOT / "prisma" / "schema.prisma").exists(), "schema.prisma is missing"
    assert (ROOT / "package.json").exists(), "package.json is missing"


def test_schema_targets_mysql_and_contains_core_models():
    schema = (ROOT / "prisma" / "schema.prisma").read_text(encoding="utf-8")
    assert 'provider = "mysql"' in schema
    assert 'model Persona' in schema
    assert 'model Session' in schema
    assert 'model Interaction' in schema
    assert 'model Reminder' in schema
    assert 'model AppUser' in schema
