# Launch checklist

This repo is the public distribution package. It does not submit a marketplace listing or publish to the MCP Registry. Checked boxes are things already done. Unchecked boxes are still someone else's step.

Reviewed against the 2026-10-07 launch notes and the official docs linked below. Re-check those docs on the day you submit. Schemas drift.

## In this repo

- [x] README with Cursor, Claude Code, and Codex install paths, OAuth, token fallback, tools, and privacy/terms links.
- [x] MIT license, copyright Cybret.
- [x] Cursor manifest (`.cursor-plugin/plugin.json`) and shared `mcp.json` at `https://mcp.cybret.ai/mcp`.
- [x] Claude Code plugin and marketplace so `/plugin marketplace add CYBRET-AI/cybret-mcp` can resolve `cybret@cybret`.
- [x] Codex / Agent Plugins manifests (root `plugin.json` and `.codex-plugin/plugin.json`).
- [x] MCP Registry `server.json` for `ai.cybret/findings` (schema 2025-12-11). Not published.
- [x] Triage skill, plus a Cursor rule.
- [x] Square icon assets from the official favicon, with derived sizes and a vector trace.
- [x] GitHub Action that validates manifests and the README endpoint.
- [x] Docs URL https://www.cybret.ai/docs/mcp and support URL https://www.cybret.ai/support. Linked from the README. Claude `documentationUrl` and `supportUrl`, and OpenAI `interface.supportURL`, point at them. Cursor's plugin manifest has no docs or support field, so those URLs stay in the README.

## MCP Registry

Docs: [remote servers](https://modelcontextprotocol.io/registry/remote-servers), [authentication](https://modelcontextprotocol.io/registry/authentication).

Namespace `ai.cybret` is DNS auth on the apex domain `cybret.ai`. The registry checks namespace ownership, not a human review.

- [ ] Generate an Ed25519 key for `mcp-publisher` and store it outside this repo.
- [ ] Add the TXT record `mcp-publisher login dns` prints to the apex `cybret.ai` zone.
- [ ] `mcp-publisher login dns --domain cybret.ai --private-key <path>`.
- [ ] `mcp-publisher publish` the `server.json` in this repo (`name` `ai.cybret/findings`, remote `https://mcp.cybret.ai/mcp`).
- [x] `websiteUrl` stays `https://www.cybret.ai`. Registry guidance treats that field as a homepage, documentation page, or project site. It does not prefer the docs URL over the product homepage. Install steps live at https://www.cybret.ai/docs/mcp. `server.json` is unchanged at version `0.1.0`.
- [ ] `repository` is omitted. The field is for server source, and the server stays private. Do not point it at this distribution repo as if the server code lived here.
- [ ] Icon URL is the public favicon `https://www.cybret.ai/favicon.png`. Replace it if a higher-resolution official icon is published.

## Cursor Marketplace and cursor.directory

Docs: [plugins](https://cursor.com/docs/plugins), [plugins reference](https://cursor.com/docs/reference/plugins). Submit at [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish). Community listing: [cursor.directory/plugins/new](https://cursor.directory/plugins/new).

- [x] Repository is public at https://github.com/CYBRET-AI/cybret-mcp.
- [ ] Install the plugin from this repo in Cursor and complete OAuth against `https://mcp.cybret.ai/mcp`.
- [ ] Confirm Cursor loads one plugin when both root `plugin.json` and `.cursor-plugin/plugin.json` exist. The docs describe the two formats as alternatives. If the IDE loads both, drop the root manifest from Cursor's discovery path before submission.
- [ ] Confirm Cursor accepts `mcp.json` with `$schema` and `type: streamable-http`. Cursor's own plugin example infers HTTP from `url`. The Agent Plugins schema requires `type`.
- [ ] cursor.directory: sign in, paste the public repo, pass the automated scan.
- [ ] Cursor Marketplace: submit the public repo for manual review.
- [x] Cursor's manifest schema (https://cursor.com/docs/reference/plugins, re-checked 2026-10-08) has no documentation or support field. Those URLs are in the README. Logo path is `assets/icon.png`. `author.email` is hello@cybret.ai.

## Claude Code marketplace

Docs: [create a marketplace](https://code.claude.com/docs/en/plugins/create-marketplace), [marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference), [manifest reference](https://code.claude.com/docs/en/plugins/manifest-reference).

- [ ] Smoke-test `claude mcp add --transport http cybret https://mcp.cybret.ai/mcp` and a real `/mcp` login. Loopback dynamic-client registration was probed on 2026-10-07. A full CLI login was not.
- [ ] With the repo readable by the tester, run `/plugin marketplace add CYBRET-AI/cybret-mcp`, then `/plugin install cybret@cybret`.
- [ ] Run `claude plugin validate .` on a machine with Claude Code. This repo's CI checks the documented required fields. It is not the Claude Code binary.

## Anthropic directory

Docs: [publish](https://claude.com/docs/directory/publish), [plugin submit](https://claude.com/docs/plugins/submit), [connector submission](https://claude.com/docs/connectors/building/submission), [authentication](https://claude.com/docs/connectors/building/authentication).

Not ready. Do not submit a connector or plugin bundle yet.

- [ ] Server: `title` plus `readOnlyHint`, `destructiveHint`, and `openWorldHint` on every tool. The 2026-10-07 review found none. Suggested values once the server changes: `list_open_findings` and `get_finding` read-only, not open-world; `mark_status` not read-only, not destructive (status changes are reversible), not open-world.
- [x] Docs URL https://www.cybret.ai/docs/mcp and support contact https://www.cybret.ai/support (hello@cybret.ai). Set on `.claude-plugin/plugin.json` as `documentationUrl` and `supportUrl`.
- [ ] Consent screen shows the client name and the redirect hostname, with a warning for loopback redirects.
- [ ] End-to-end custom connector on claude.ai. The authorization redirect was a 302 into the app, not an HTTP 307, but a real claude.ai connector test is still required. The claude.ai callback rejects a 307.
- [ ] Reviewer tenant with seeded findings, on a paid Claude plan (Team or Enterprise owner) for the directory portal.
- [x] Privacy policy returns 200 at `https://www.cybret.ai/privacy` and includes [AI agents and MCP connections](https://www.cybret.ai/privacy#ai-agents-and-mcp-connections) (customer data returned to the AI client, OAuth or agent token, workspace and scope limits). Terms remain https://www.cybret.ai/terms. Directory reviewers still have to accept that text.
- [ ] After the server fixes: submit the MCP connector (URL only) and, separately, this public repo as the plugin bundle, then pair them.
- [x] `.claude-plugin/plugin.json` sets `documentationUrl`, `supportUrl`, `privacyPolicyUrl`, and `termsOfServiceUrl`. `author.email` is hello@cybret.ai. Claude Code's manifest reference accepts these directory-listing fields (`claude plugin validate` on v2.1.281 or later; earlier versions warn, and `--strict` fails on the warning). This environment does not have the Claude Code binary, so CI checks the field names against that reference rather than running `claude plugin validate`.

## Codex CLI

Docs: [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp.md), [config reference](https://developers.openai.com/codex/config-reference).

- [ ] Smoke-test `codex mcp add cybret --url https://mcp.cybret.ai/mcp` and `codex mcp login cybret`. Loopback registration was probed. A full CLI login was not.
- [ ] No separate Codex marketplace submission. Direct CLI use does not wait on the directory.

## OpenAI plugin directory (ChatGPT and Codex)

Docs: [submission](https://developers.openai.com/plugins/deploy/submission), [app review](https://developers.openai.com/plugins/deploy/app-review), [auth](https://developers.openai.com/plugins/build/auth), [packaging](https://developers.openai.com/plugins/build/plugins).

Not ready. Do not upload the ZIP yet.

- [ ] Allow the ChatGPT OAuth callback `https://chatgpt.com/connector/oauth/{callback_id}` and the legacy `https://chatgpt.com/connector_platform_oauth_redirect`. Both were rejected with `invalid_redirect_uri` on 2026-10-07.
- [ ] Serve the domain-verification token at `https://mcp.cybret.ai/.well-known/openai-apps-challenge` (or an allowed parent).
- [ ] Tool annotations and per-annotation justifications for the scanner (`readOnlyHint`, `destructiveHint`, `openWorldHint`).
- [x] `interface.supportURL` is https://www.cybret.ai/support on root `plugin.json` and `.codex-plugin/plugin.json`. `websiteURL` stays https://www.cybret.ai. `privacyPolicyURL` and `termsOfServiceURL` stay https://www.cybret.ai/privacy and https://www.cybret.ai/terms.
- [x] The privacy policy's AI agents and MCP connections section discloses the customer data the MCP server returns to the AI client (identifiers, titles, severities, statuses, locations, evidence, remediation), and that the client provider is not a Cybret subprocessor.
- [ ] `review.demo_recording_url` is omitted. Record a demo and add the URL before submission. Final submission requires it.
- [ ] Draft positive (5) and negative (3) test cases are in the manifests so reviewers of this repo can edit them. Rerun them against a seeded reviewer tenant before submit. They assume the tool names from the server review, which this repo could not re-fetch.
- [ ] Reviewer account that can sign in without MFA, email codes, or magic links.
- [ ] Verified individual or business identity. Org owner or `api.apps.write`. Project without EU data residency.
- [ ] Server origin stays `https://mcp.cybret.ai/mcp` after publish. It cannot change later.
- [ ] No custom UI, so do not add screenshots.
- [ ] When the blockers above are gone: build the ZIP from this repo (root `plugin.json`, `mcp.json`, `.codex-plugin/plugin.json`, `.mcp.json`, `skills/`, `assets/`), upload, verify the domain, scan tools, and submit.

## Server-side blockers

These are product and server changes. They are not fixed by this repo, and server code must not be copied here.

- [ ] Tool `title` and annotations. None were present in the 2026-10-07 review. Hard requirement for the Anthropic directory. OpenAI's scanner flags missing hints.
- [ ] ChatGPT OAuth redirect URIs, as above.
- [ ] OpenAI domain-verification route.
- [x] Docs URL https://www.cybret.ai/docs/mcp and support URL https://www.cybret.ai/support are live (HTTP 200 on 2026-10-08).
- [ ] Consent page shows the OAuth client name and redirect host, plus a loopback warning.
- [ ] Development-mode flag on production. The launch review found `APISCAN_CONTROL_DEVELOPMENT_MODE` enabled and flagged dev-mode code paths, including billing admission metering. Decide it is off, or write down exactly what it still gates, before any directory submission.
- [x] `list_open_findings` filters. https://www.cybret.ai/docs/mcp (2026-10-08) documents optional `severity`, optional `target`, and `limit` (1–100, default 25). This repo has not re-called `tools/list`.
- [ ] Tool errors come back as an `{"error": ...}` payload on a successful result, not as an MCP `isError`. Clients cannot tell failure from success. The triage skill tells agents to treat that payload as failure.
- [ ] Server `instructions` are a single line. An empty tenant returns `[]` with no hint to scan. The skill covers that hint on the client.
- [ ] CIMD is not advertised. Claude and Codex fall back to dynamic client registration, which is enough for CLI launch and grows a client row per registration. Consider CIMD before directory-scale traffic.
- [ ] Browser CORS preflight is not required for Cursor, Claude Code, Codex CLI, claude.ai, or ChatGPT. It still matters for browser-based inspectors.

## What not to do from this repo

- The GitHub repository is already public. Do not run `mcp-publisher publish`.
- Do not submit Cursor Marketplace, cursor.directory, the Anthropic directory, or the OpenAI plugin directory.
- Do not put access tokens, OAuth client secrets, or the DNS private key in git.
