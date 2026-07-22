from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from importlib import import_module
from pathlib import Path
from typing import Any, get_args

from pydantic import AliasChoices, SecretBytes, SecretStr
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
from pydantic_settings import BaseSettings

ROOT_DIR = Path(__file__).resolve().parents[1]
SECRET_FIELD_MARKERS = ("api_key", "secret", "token", "password")


@dataclass(frozen=True)
class EnvExampleTarget:
    project_root: Path
    src_dir: Path
    settings_class: str
    output: Path
    header_lines: tuple[str, ...]
    path_as_posix: bool = False

    @property
    def project(self) -> str:
        return self.project_root.as_posix()


ENV_EXAMPLE_TARGETS: tuple[EnvExampleTarget, ...] = (
    EnvExampleTarget(
        project_root=Path("."),
        src_dir=Path("."),
        settings_class="backend.config.settings.Settings",
        output=Path(".env.example"),
        header_lines=(
            "# 由 backend.config.settings.Settings 自动生成。",
            "# 请勿在此文件中填写真实密钥。",
            "",
        ),
    ),
)


def _repo_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return ROOT_DIR / path


def get_target(project: str) -> EnvExampleTarget:
    normalized_project = Path(project).as_posix()
    for target in ENV_EXAMPLE_TARGETS:
        if target.project == normalized_project:
            return target
    supported = ", ".join(target.project for target in ENV_EXAMPLE_TARGETS)
    raise ValueError(f"Unsupported env example project {project!r}. Supported: {supported}")


def _ensure_import_path(target: EnvExampleTarget) -> None:
    src_dir = str(_repo_path(target.src_dir))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)


def load_settings_class(target: EnvExampleTarget) -> type[BaseSettings]:
    _ensure_import_path(target)
    module_path, _, class_name = target.settings_class.rpartition(".")
    if not module_path or not class_name:
        raise ValueError(f"Invalid settings class path: {target.settings_class}")

    settings_class = getattr(import_module(module_path), class_name)
    if not isinstance(settings_class, type) or not issubclass(settings_class, BaseSettings):
        raise TypeError(f"{target.settings_class} is not a pydantic-settings BaseSettings class")
    return settings_class


def _annotation_contains_secret(annotation: Any) -> bool:
    if annotation in {SecretStr, SecretBytes}:
        return True
    return any(_annotation_contains_secret(arg) for arg in get_args(annotation))


def _is_secret_field(field_name: str, field: FieldInfo) -> bool:
    return _annotation_contains_secret(field.annotation) or any(
        marker in field_name.lower() for marker in SECRET_FIELD_MARKERS
    )


def _env_name(
    field_name: str,
    field: FieldInfo,
    settings_class: type[BaseSettings],
) -> str:
    alias = field.validation_alias
    if isinstance(alias, str):
        return alias
    if isinstance(alias, AliasChoices):
        first_string_alias = next(
            (choice for choice in alias.choices if isinstance(choice, str)),
            None,
        )
        if first_string_alias:
            return first_string_alias

    env_prefix = settings_class.model_config.get("env_prefix") or ""
    return f"{env_prefix}{field_name}".upper()


def _default_to_env_value(
    field_name: str,
    field: FieldInfo,
    *,
    path_as_posix: bool = False,
) -> str:
    if _is_secret_field(field_name, field):
        return ""

    value = field.default
    if value is PydanticUndefined or value is None:
        return ""
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, Path):
        return value.as_posix() if path_as_posix else str(value)
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return str(value)


def build_env_example(
    settings_class: type[BaseSettings] | None = None,
    *,
    target: EnvExampleTarget | None = None,
    header_lines: Sequence[str] | None = None,
    path_as_posix: bool | None = None,
) -> str:
    if settings_class is None:
        if target is None:
            raise ValueError("target is required when settings_class is not provided")
        settings_class = load_settings_class(target)

    if header_lines is not None:
        lines = list(header_lines)
    elif target is not None:
        lines = list(target.header_lines)
    else:
        lines = []

    if path_as_posix is None and target is not None:
        use_posix_paths = target.path_as_posix
    else:
        use_posix_paths = bool(path_as_posix)

    for field_name, field in settings_class.model_fields.items():
        if field.description:
            lines.append(f"# {field.description}")
        lines.append(
            f"{_env_name(field_name, field, settings_class)}="
            f"{_default_to_env_value(field_name, field, path_as_posix=use_posix_paths)}"
        )

    return "\n".join(lines) + "\n"


def write_env_example(
    target: EnvExampleTarget,
    *,
    output_file: Path | None = None,
    settings_class: type[BaseSettings] | None = None,
) -> bool:
    output_path = output_file or _repo_path(target.output)
    content = build_env_example(settings_class, target=target)
    if output_path.exists() and output_path.read_text(encoding="utf-8") == content:
        return False
    output_path.write_text(content, encoding="utf-8")
    return True


def check_env_example(target: EnvExampleTarget, *, output_file: Path | None = None) -> bool:
    output_path = output_file or _repo_path(target.output)
    current = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
    expected = build_env_example(target=target)
    if current == expected:
        return True

    print(
        f"{target.output.as_posix()} is out of date. "
        f"Run `uv run python scripts/generate_env_examples.py --project {target.project}`.",
        file=sys.stderr,
    )
    return False


def _selected_targets(project: str | None) -> tuple[EnvExampleTarget, ...]:
    if project is None:
        return ENV_EXAMPLE_TARGETS
    return (get_target(project),)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate app .env.example files.")
    parser.add_argument(
        "--project",
        choices=[target.project for target in ENV_EXAMPLE_TARGETS],
        help="Only generate/check one app target, for example apps/ocr_app.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Override output path. Only valid when --project selects one target.",
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    if args.output is not None and args.project is None:
        parser.error("--output can only be used together with --project")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    targets = _selected_targets(args.project)

    if args.check:
        checks_passed = all(check_env_example(target, output_file=args.output) for target in targets)
        return 0 if checks_passed else 1

    for target in targets:
        changed = write_env_example(target, output_file=args.output)
        output = args.output or target.output
        if changed:
            print(f"Updated {output.as_posix()}")
        else:
            print(f"{output.as_posix()} is already up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
