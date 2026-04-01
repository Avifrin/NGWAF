# rules/rules.py
import yaml
import re
import os
from pathlib import Path

# Путь к YAML файлам
RULES_DIR = Path(__file__).parent / "rules"


def load_rules(rule_type: str = "all", severity_threshold: float = 0.5):
    """Загрузка с фильтром по типу и серьезности"""
    patterns = []
    rules_dir = Path(__file__).parent / "rules"

    for yaml_file in rules_dir.glob("*.yaml"):
        with open(yaml_file, 'r', encoding='utf-8') as f:
            rules_data = yaml.safe_load(f) or {}

        for rule_name, config in rules_data.items():
            if config.get("severity", 0) < severity_threshold:
                continue
            if rule_type != "all" and config.get("type") != rule_type:
                continue

            try:
                regex = re.compile(config["pattern"], re.IGNORECASE | re.DOTALL)
                patterns.append((regex, config["tag"], config["severity"]))
            except re.error:
                print(f"⚠️ Invalid regex in {yaml_file}:{rule_name}")

    return patterns


# Кэшируем все правила
PATTERNS = load_rules()
CRITICAL_PATTERNS = load_rules(severity_threshold=0.8)
