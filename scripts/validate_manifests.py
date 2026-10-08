#!/usr/bin/env python3
"""Validate Cybret MCP distribution manifests.

Official JSON Schemas (fetched 2026-10-07, vendored under schemas/):

- https://agent-plugins.org/schemas/1.0.0/plugin.schema.json
- https://agent-plugins.org/schemas/1.0.0/mcp.schema.json
- https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json

Cursor, Claude Code, and Codex publish field lists rather than a single
machine-readable manifest schema. Those files are checked against the
required fields and constraints in the docs cited in LAUNCH.md.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from jsonschema import Draft7Validator, Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
MCP_URL = "https://mcp.cybret.ai/mcp"
ALLOWED_MCP_URLS = {
    MCP_URL,
    "https://mcp.cybret.ai/.well-known/oauth-protected-resource/mcp",
    "https://mcp.cybret.ai/.well-known/oauth-authorization-server",
    "https://mcp.cybret.ai/.well-known/openai-apps-challenge",
}
OPENAI_CATEGORIES = {
    "Productivity",
    "Creativity",
    "Developer Tools",
    "Business & Operations",
    "Data & Analytics",
    "Communication",
    "Education & Research",
    "Security",
    "Finance",
    "Healthcare",
    "Travel",
    "Entertainment",
    "Other",
}
PNG_SIZES = {
    "assets/icon.png": 256,
    "assets/icon-48.png": 48,
    "assets/icon-128.png": 128,
    "assets/icon-512.png": 512,
    "assets/icon-dark.png": 256,
    "assets/logo.png": 512,
    "assets/logo-dark.png": 512,
}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]{20,}"),
)

errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def load_json(rel: str) -> dict:
    path = ROOT / rel
    if not path.is_file():
        fail(f"missing {rel}")
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{rel} is not valid JSON: {exc}")
        return {}
    if not isinstance(data, dict):
        fail(f"{rel} must be a JSON object")
        return {}
    return data


def validate_schema(rel: str, schema_rel: str, validator_cls) -> dict:
    instance = load_json(rel)
    schema_path = ROOT / schema_rel
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = validator_cls(schema)
    for err in sorted(validator.iter_errors(instance), key=lambda item: list(item.path)):
        loc = "/".join(str(part) for part in err.path) or "<root>"
        fail(f"{rel} schema: {loc}: {err.message}")
    return instance


def require(cond: bool, message: str) -> None:
    if not cond:
        fail(message)


def png_size(rel: str) -> tuple[int, int]:
    data = (ROOT / rel).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        fail(f"{rel} is not a PNG")
        return (0, 0)
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    return width, height


def check_relative(rel_file: str, value: str, label: str) -> None:
    require(isinstance(value, str) and value != "", f"{rel_file} {label} must be a non-empty string")
    if not isinstance(value, str):
        return
    require(not value.startswith(("/", "\\")), f"{rel_file} {label} must be relative")
    require(".." not in Path(value).parts, f"{rel_file} {label} must not contain ..")
    target = (ROOT / value.removeprefix("./")).resolve()
    require(str(target).startswith(str(ROOT.resolve())), f"{rel_file} {label} escapes the repo")
    require(target.exists(), f"{rel_file} {label} missing: {value}")


def server_entry_url(document: dict, rel: str) -> None:
    servers = document.get("mcpServers")
    require(isinstance(servers, dict) and "cybret" in servers, f"{rel} must define mcpServers.cybret")
    if not isinstance(servers, dict):
        return
    entry = servers.get("cybret")
    require(isinstance(entry, dict), f"{rel} cybret entry must be an object")
    if isinstance(entry, dict):
        require(entry.get("url") == MCP_URL, f"{rel} cybret url must be {MCP_URL}")


def check_openai_interface(interface: dict, rel: str) -> None:
    require(interface.get("displayName") == "Cybret", f"{rel} displayName")
    short = interface.get("shortDescription", "")
    require(isinstance(short, str) and 0 < len(short) <= 30, f"{rel} shortDescription must be 1-30 chars")
    require(interface.get("category") in OPENAI_CATEGORIES, f"{rel} category is not a directory category")
    require(interface.get("developerName") == "Cybret", f"{rel} developerName must match author name")
    require(interface.get("websiteURL") == "https://www.cybret.ai", f"{rel} websiteURL")
    require(interface.get("supportURL") == "https://www.cybret.ai/support", f"{rel} supportURL")
    require(interface.get("privacyPolicyURL") == "https://www.cybret.ai/privacy", f"{rel} privacyPolicyURL")
    require(interface.get("termsOfServiceURL") == "https://www.cybret.ai/terms", f"{rel} termsOfServiceURL")
    prompts = interface.get("defaultPrompt")
    require(isinstance(prompts, list) and len(prompts) <= 3, f"{rel} defaultPrompt max 3")
    if isinstance(prompts, list):
        for prompt in prompts:
            require(isinstance(prompt, str) and 0 < len(prompt) <= 128, f"{rel} defaultPrompt entry length")
            require("@" not in prompt, f"{rel} defaultPrompt must not mention an MCP server")
    for key in ("composerIcon", "composerIconDark", "logo", "logoDark"):
        check_relative(rel, interface.get(key, ""), key)


def check_review(review: dict, rel: str) -> None:
    require("demo_recording_url" not in review, f"{rel} must omit demo_recording_url until a recording exists")
    cases = review.get("test_cases", {})
    positive = cases.get("positive")
    negative = cases.get("negative")
    require(isinstance(positive, list) and len(positive) == 5, f"{rel} needs exactly 5 positive test cases")
    require(isinstance(negative, list) and len(negative) == 3, f"{rel} needs exactly 3 negative test cases")
    if isinstance(positive, list):
        for case in positive:
            for field in ("description", "prompt", "tools_triggered", "expected_behavior"):
                require(isinstance(case.get(field), str) and case[field].strip(), f"{rel} positive case {field}")
    if isinstance(negative, list):
        for case in negative:
            for field in ("description", "prompt"):
                require(isinstance(case.get(field), str) and case[field].strip(), f"{rel} negative case {field}")


def check_readme() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    required = [
        "claude mcp add --transport http cybret https://mcp.cybret.ai/mcp",
        "/plugin marketplace add CYBRET-AI/cybret-mcp",
        "/plugin install cybret@cybret",
        "codex mcp add cybret --url https://mcp.cybret.ai/mcp",
        "codex mcp login cybret",
        "cursor://anysphere.cursor-deeplink/mcp/install?name=cybret&config=eyJ1cmwiOiJodHRwczovL21jcC5jeWJyZXQuYWkvbWNwIn0=",
        '"type": "streamable-http"',
        '"url": "https://mcp.cybret.ai/mcp"',
        "https://www.cybret.ai/docs/mcp",
        "https://www.cybret.ai/support",
        "https://www.cybret.ai/privacy",
        "https://www.cybret.ai/privacy#ai-agents-and-mcp-connections",
        "https://www.cybret.ai/terms",
        "## Docs and support",
        "hello@cybret.ai",
        "security@cybret.ai",
        "findings:read",
        "findings:write",
        "list_open_findings",
        "get_finding",
        "mark_status",
        "https://app.cybret.ai/settings/agents",
    ]
    for snippet in required:
        require(snippet in text, f"README.md missing install or reference snippet: {snippet}")
    urls = mcp_urls(text)
    require(urls <= ALLOWED_MCP_URLS, f"README.md has unexpected mcp.cybret.ai URLs: {urls - ALLOWED_MCP_URLS}")


def mcp_urls(text: str) -> set[str]:
    found = re.findall(r"https://mcp\.cybret\.ai[^\s)\"'`]*", text)
    return {url.rstrip(".,;") for url in found}


def check_secrets_and_endpoints() -> None:
    server_path = "src/" + "api_scanner"
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() in {".png", ".woff", ".woff2"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(ROOT).as_posix()
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                fail(f"{rel} matches secret pattern {pattern.pattern}")
        extra = mcp_urls(text) - ALLOWED_MCP_URLS
        require(not extra, f"{rel} has unexpected mcp.cybret.ai URLs: {sorted(extra)}")
        if rel not in {"README.md", "LAUNCH.md"} and server_path in text:
            fail(f"{rel} must not vendor server code")


def main() -> int:
    plugin = validate_schema(
        "plugin.json",
        "schemas/agent-plugins-plugin.schema.json",
        Draft202012Validator,
    )
    mcp = validate_schema(
        "mcp.json",
        "schemas/agent-plugins-mcp.schema.json",
        Draft202012Validator,
    )
    server = validate_schema(
        "server.json",
        "schemas/mcp-registry-server.schema.json",
        Draft7Validator,
    )
    server_entry_url(mcp, "mcp.json")
    require(mcp.get("mcpServers", {}).get("cybret", {}).get("type") == "streamable-http", "mcp.json type")

    require(server.get("name") == "ai.cybret/findings", "server.json name")
    description = server.get("description", "")
    require(isinstance(description, str) and len(description) <= 100, "server.json description length")
    remotes = server.get("remotes")
    require(
        isinstance(remotes, list)
        and len(remotes) == 1
        and remotes[0].get("type") == "streamable-http"
        and remotes[0].get("url") == MCP_URL,
        "server.json remote",
    )
    require("repository" not in server, "server.json must not claim this repo is the server source")
    require(server.get("version") == "0.1.0", "server.json version stays 0.1.0 until the document changes")
    require(server.get("websiteUrl") == "https://www.cybret.ai", "server.json websiteUrl stays the product homepage")

    dot_mcp = load_json(".mcp.json")
    server_entry_url(dot_mcp, ".mcp.json")
    require(dot_mcp.get("mcpServers", {}).get("cybret", {}).get("type") == "http", ".mcp.json type must be http")

    cursor = load_json(".cursor-plugin/plugin.json")
    require(cursor.get("name") == "cybret", "cursor name")
    require(re.fullmatch(r"[a-z0-9]+(?:[.-][a-z0-9]+)*", cursor.get("name", "")) is not None, "cursor kebab name")
    require(isinstance(cursor.get("description"), str) and cursor["description"].strip(), "cursor description")
    require(cursor.get("mcpServers") == "./mcp.json", "cursor mcpServers path")
    check_relative(".cursor-plugin/plugin.json", cursor.get("logo", ""), "logo")
    check_relative(".cursor-plugin/plugin.json", cursor.get("skills", ""), "skills")
    check_relative(".cursor-plugin/plugin.json", cursor.get("rules", ""), "rules")
    cursor_fields = {
        "name",
        "version",
        "description",
        "author",
        "homepage",
        "repository",
        "license",
        "keywords",
        "logo",
        "rules",
        "agents",
        "skills",
        "commands",
        "hooks",
        "mcpServers",
        "variables",
    }
    unknown_cursor = sorted(set(cursor) - cursor_fields)
    require(not unknown_cursor, f"cursor manifest has fields the Cursor schema does not list: {unknown_cursor}")
    require(cursor.get("author", {}).get("email") == "hello@cybret.ai", "cursor author.email")

    claude = load_json(".claude-plugin/plugin.json")
    require(claude.get("name") == "cybret", "claude plugin name")
    require(claude.get("mcpServers") == "./.mcp.json", "claude mcpServers path")
    require(claude.get("documentationUrl") == "https://www.cybret.ai/docs/mcp", "claude documentationUrl")
    require(claude.get("supportUrl") == "https://www.cybret.ai/support", "claude supportUrl")
    require(claude.get("privacyPolicyUrl") == "https://www.cybret.ai/privacy", "claude privacyPolicyUrl")
    require(claude.get("termsOfServiceUrl") == "https://www.cybret.ai/terms", "claude termsOfServiceUrl")
    require(claude.get("author", {}).get("email") == "hello@cybret.ai", "claude author.email")
    check_relative(".claude-plugin/plugin.json", claude.get("icon", ""), "icon")

    market = load_json(".claude-plugin/marketplace.json")
    require(market.get("name") == "cybret", "marketplace name")
    require(isinstance(market.get("owner"), dict) and market["owner"].get("name"), "marketplace owner.name")
    require(isinstance(market.get("description"), str) and market["description"].strip(), "marketplace description")
    plugins = market.get("plugins")
    require(isinstance(plugins, list) and len(plugins) == 1, "marketplace plugins")
    if isinstance(plugins, list) and plugins:
        entry = plugins[0]
        require(entry.get("name") == "cybret", "marketplace plugin name")
        require(entry.get("source") == "./", "marketplace plugin source must be ./")

    codex = load_json(".codex-plugin/plugin.json")
    require(codex.get("name") == "cybret", "codex name")
    require(codex.get("version") == "0.1.0", "codex version")
    require(codex.get("skills") == "./skills/", "codex skills path")
    require(codex.get("mcpServers") == "./.mcp.json", "codex mcpServers must be ./.mcp.json")
    require(codex.get("author", {}).get("name") == "Cybret", "codex author.name")
    require(codex.get("author", {}).get("email") == "hello@cybret.ai", "codex author.email")
    notes = codex.get("extensions", {}).get("com.openai", {}).get("publication", {}).get("release_notes", "")
    lowered = notes.lower() if isinstance(notes, str) else ""
    require("blocked on docs" not in lowered, "release notes must not list docs as a blocker")
    require("demo recording" in lowered, "release notes still name the demo-recording blocker")
    check_openai_interface(codex.get("interface", {}), ".codex-plugin/plugin.json")
    codex_ext = codex.get("extensions", {}).get("com.openai", {})
    check_review(codex_ext.get("review", {}), ".codex-plugin/plugin.json")
    check_relative(".codex-plugin/plugin.json", codex_ext.get("onboardingSkill", ""), "onboardingSkill")

    root_ext = plugin.get("extensions", {}).get("com.openai", {})
    require(root_ext.get("interface") == codex.get("interface"), "root and codex interface drifted")
    require(root_ext.get("review") == codex_ext.get("review"), "root and codex review drifted")
    require(root_ext.get("onboardingSkill") == codex_ext.get("onboardingSkill"), "onboarding skill drifted")
    require(root_ext.get("publication") == codex_ext.get("publication"), "release notes drifted")
    require(plugin.get("author", {}).get("email") == "hello@cybret.ai", "root plugin author.email")
    require(market.get("owner", {}).get("email") == "hello@cybret.ai", "marketplace owner.email")

    skill = ROOT / "skills/triage-cybret-findings/SKILL.md"
    skill_text = skill.read_text(encoding="utf-8")
    require(skill_text.startswith("---\n"), "skill frontmatter")
    require("name: triage-cybret-findings" in skill_text, "skill name")
    for tool in ("list_open_findings", "get_finding", "mark_status"):
        require(tool in skill_text, f"skill missing {tool}")
    require("findings:write" in skill_text and "findings:read" in skill_text, "skill scopes")

    rule = (ROOT / "rules/triage-cybret-findings.mdc").read_text(encoding="utf-8")
    require("alwaysApply: false" in rule, "cursor rule must not always apply")
    require("mark_status" in rule and "list_open_findings" in rule, "cursor rule steps")

    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    require("MIT License" in license_text and "Copyright (c) 2026 Cybret" in license_text, "LICENSE copyright")

    for rel, size in PNG_SIZES.items():
        width, height = png_size(rel)
        require(width == size and height == size, f"{rel} must be {size}x{size}, got {width}x{height}")
    require((ROOT / "assets/icon.svg").is_file(), "assets/icon.svg")
    require((ROOT / "assets/icon-dark.svg").is_file(), "assets/icon-dark.svg")

    check_readme()
    check_secrets_and_endpoints()

    if errors:
        print(f"{len(errors)} manifest check(s) failed:", file=sys.stderr)
        for message in errors:
            print(f"- {message}", file=sys.stderr)
        return 1
    print("manifest checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
