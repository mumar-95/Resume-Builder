"""Categorize technologies into recruiter-friendly skill groups."""

from __future__ import annotations

import re

CATEGORY_ORDER = [
    "ETL Tools",
    "Databases",
    "Cloud Technologies",
    "Programming Languages",
    "Scheduling Tools",
    "Data Modeling & Transformation",
    "Testing & Quality",
    "DevOps & Platforms",
    "Development Methodologies",
    "Other Technical Skills",
]

_RULES: list[tuple[str, tuple[str, ...]]] = [
    (
        "ETL Tools",
        (
            "informatica",
            "powercenter",
            "iics",
            "idmc",
            "talend",
            "dataStage",
            "datastage",
            "ssis",
            "ab initio",
            "abinitio",
            "pentaho",
            "matillion",
            "fivetran",
            "airbyte",
            "glue",
            "adf",
            "data factory",
        ),
    ),
    (
        "Databases",
        (
            "oracle",
            "sql server",
            "mssql",
            "mysql",
            "postgres",
            "postgresql",
            "mongodb",
            "dynamodb",
            "cassandra",
            "redis",
            "snowflake",
            "redshift",
            "bigquery",
            "teradata",
            "db2",
            "hana",
            "synapse",
            "sql",
            "pl/sql",
            "tsql",
            "t-sql",
        ),
    ),
    (
        "Cloud Technologies",
        (
            "aws",
            "azure",
            "gcp",
            "google cloud",
            "s3",
            "ec2",
            "lambda",
            "cloudformation",
            "terraform",
            "snowpipe",
            "databricks",
            "synapse",
        ),
    ),
    (
        "Programming Languages",
        (
            "python",
            "java",
            "scala",
            "javascript",
            "typescript",
            "c#",
            "c++",
            "go",
            "golang",
            "kotlin",
            "ruby",
            "perl",
            "shell",
            "bash",
            "unix",
            "linux",
            "powershell",
        ),
    ),
    (
        "Scheduling Tools",
        (
            "control-m",
            "controlm",
            "autosys",
            "airflow",
            "composer",
            "cron",
            "tws",
            "esp",
            "jenkins",
            "gitlab ci",
            "github actions",
        ),
    ),
    (
        "Data Modeling & Transformation",
        (
            "dbt",
            "dbt core",
            "spark",
            "pyspark",
            "hadoop",
            "hive",
            "kafka",
            "streams",
            "tasks",
            "scd",
            "dimensional",
            "star schema",
            "data modeling",
        ),
    ),
    (
        "Testing & Quality",
        (
            "selenium",
            "junit",
            "pytest",
            "testng",
            "cucumber",
            "postman",
            "soapui",
            "quality center",
            "almq",
            "tosca",
        ),
    ),
    (
        "DevOps & Platforms",
        (
            "docker",
            "kubernetes",
            "k8s",
            "git",
            "github",
            "gitlab",
            "bitbucket",
            "jira",
            "confluence",
            "ansible",
            "maven",
            "gradle",
            "npm",
        ),
    ),
    (
        "Development Methodologies",
        (
            "agile",
            "scrum",
            "kanban",
            "waterfall",
            "sdlc",
            "devops",
            "ci/cd",
            "cicd",
        ),
    ),
]


def categorize_skills(technologies: list[str]) -> dict[str, list[str]]:
    """Group technologies into professional categories; preserve first-seen order."""
    grouped: dict[str, list[str]] = {name: [] for name in CATEGORY_ORDER}
    seen: set[str] = set()

    for tech in technologies:
        label = (tech or "").strip()
        if not label:
            continue
        key = label.lower()
        if key in seen:
            continue
        seen.add(key)
        category = _match_category(label)
        grouped[category].append(label)

    return {name: values for name, values in grouped.items() if values}


def _match_category(tech: str) -> str:
    lower = tech.lower().strip()
    compact = re.sub(r"[^a-z0-9]+", "", lower)
    for category, tokens in _RULES:
        for token in tokens:
            token_compact = re.sub(r"[^a-z0-9]+", "", token.lower())
            if token.lower() in lower or token_compact in compact:
                return category
    return "Other Technical Skills"
