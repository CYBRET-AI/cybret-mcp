# Cybret MCP

Cybret ([app.cybret.ai](https://app.cybret.ai)) finds API and application vulnerabilities and validates them before they reach an engineer. This repository is the public plugin and install surface for the hosted Cybret MCP server. The server itself stays private.

Coding agents use it to pull those validated findings into the editor, apply the remediation in the repo they already have open, and mark the finding once the fix is on a pull request. The result is a short loop on confirmed issues, not a dump of unscored scanner noise.

The server is Streamable HTTP at `https://mcp.cybret.ai/mcp`. Sign-in is OAuth 2.1 with PKCE S256 and dynamic client registration. A personal agent token is the fallback when a client cannot complete OAuth.

You need a Cybret account that has already run a scan. This server does not start scans. With no completed scans, the findings list is empty.

## Install

Every client below points at the same endpoint: `https://mcp.cybret.ai/mcp`.

### Cursor

One click installs the remote server and prompts before adding it:

[Add Cybret to Cursor](cursor://anysphere.cursor-deeplink/mcp/install?name=cybret&config=eyJ1cmwiOiJodHRwczovL21jcC5jeWJyZXQuYWkvbWNwIn0=)

That link is the [Cursor MCP install link](https://cursor.com/docs/mcp/install-links) for this config:

```json
{
  "url": "https://mcp.cybret.ai/mcp"
}
```

To install the plugin (server, triage skill, and rule) from this repo once it is public, submit or add it from the Cursor Marketplace. Locally, copy the repo and load it as a Cursor plugin. The manifest is `.cursor-plugin/plugin.json`, and it uses the shared [`mcp.json`](mcp.json).

Manual `~/.cursor/mcp.json` or `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "cybret": {
      "url": "https://mcp.cybret.ai/mcp"
    }
  }
}
```

Cursor treats a `url` entry as Streamable HTTP and starts OAuth when the server asks for it.

### Claude Code

Direct HTTP install:

```bash
claude mcp add --transport http cybret https://mcp.cybret.ai/mcp
```

Then authenticate with `/mcp`.

From this marketplace, after the repository is reachable:

```text
/plugin marketplace add CYBRET-AI/cybret-mcp
/plugin install cybret@cybret
```

The catalog is [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json). The plugin manifest is [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json), and the server entry is [`.mcp.json`](.mcp.json) (`type` `http`, which Claude Code accepts as Streamable HTTP).

### Codex

```bash
codex mcp add cybret --url https://mcp.cybret.ai/mcp
codex mcp login cybret
```

`codex mcp login` runs OAuth for the Streamable HTTP server. The plugin package for the shared ChatGPT and Codex directory is the root [`plugin.json`](plugin.json) (Agent Plugins 1.0, with OpenAI listing fields under `extensions.com.openai`) plus [`mcp.json`](mcp.json). [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json) is the compatibility manifest and points at [`.mcp.json`](.mcp.json).

### Generic `mcp.json`

Portable Agent Plugins / MCP config, the same document checked in as [`mcp.json`](mcp.json):

```json
{
  "mcpServers": {
    "cybret": {
      "type": "streamable-http",
      "url": "https://mcp.cybret.ai/mcp"
    }
  }
}
```

Clients that expect the HTTP alias use `"type": "http"` with the same URL. That is [`.mcp.json`](.mcp.json).

## Sign in with OAuth

1. The client calls `https://mcp.cybret.ai/mcp` without a token.
2. The server answers `401` with `WWW-Authenticate: Bearer` and `resource_metadata="https://mcp.cybret.ai/.well-known/oauth-protected-resource/mcp"`.
3. The client reads that protected-resource metadata, then the authorization-server metadata at `https://mcp.cybret.ai/.well-known/oauth-authorization-server`.
4. The client registers with dynamic client registration when it does not already have a client id. The server supports authorization-code plus refresh tokens, PKCE method `S256`, and token auth methods `none`, `client_secret_post`, and `client_secret_basic`.
5. The browser opens the Cybret consent screen. Approve the scopes the client requested.
6. The client stores the access token and sends it as `Authorization: Bearer` on later MCP requests.

Scopes advertised by the protected-resource metadata:

| Scope | Use |
| --- | --- |
| `findings:read` | List and read findings. |
| `findings:write` | Update finding status (`mark_status`). |

Approve read access to triage. Approve write access only if the agent should update status.

## Token fallback

If the client cannot complete OAuth, create a personal agent token in the Cybret console: [app.cybret.ai/settings/agents](https://app.cybret.ai/settings/agents), then Advanced, Access tokens. Send it as a bearer header. The plugin manifests do not contain a token. Set one only in your own client config, and do not commit it.

Cursor example, with the token in the environment rather than the file:

```json
{
  "mcpServers": {
    "cybret": {
      "url": "https://mcp.cybret.ai/mcp",
      "headers": {
        "Authorization": "Bearer ${env:CYBRET_AGENT_TOKEN}"
      }
    }
  }
}
```

A header on the request skips the OAuth login. The token's own scopes decide whether status updates are allowed.

## Tools

The live server requires a credential, so this package could not call `tools/list`. Protected-resource metadata fetched from `https://mcp.cybret.ai/.well-known/oauth-protected-resource/mcp` on 2026-10-07 advertises `findings:read` and `findings:write`. Tool names below are from the same day's review of the private server (`src/api_scanner/mcp/server.py`). Argument names were not re-checked here. Agents must use the input schema the connected server advertises.

| Tool | Scope | Behavior described by that review |
| --- | --- | --- |
| `list_open_findings` | `findings:read` | Returns the tenant's open findings. No severity, repository, or pagination arguments. |
| `get_finding` | `findings:read` | Returns one finding, including the explanation and remediation guidance. |
| `mark_status` | `findings:write` | Updates a finding's status. The review describes a pull-request link argument. |

The triage workflow is [`skills/triage-cybret-findings/SKILL.md`](skills/triage-cybret-findings/SKILL.md). Cursor also loads [`rules/triage-cybret-findings.mdc`](rules/triage-cybret-findings.mdc).

## Security and privacy

- The credential selects the tenant. OAuth is the signed-in Cybret user. An agent token is the user who created it. The server does not accept a tenant id that would cross that boundary.
- `findings:read` can list and read findings. `findings:write` can change status. Connect read-only when the agent should not update Cybret.
- Do not commit tokens, and do not paste them into chat. The checked-in configs contain only `https://mcp.cybret.ai/mcp`.
- Customer findings are customer data. How Cybret handles personal information is in the [privacy policy](https://www.cybret.ai/privacy). Use of the service is covered by the [terms](https://www.cybret.ai/terms).

## TODO: docs and support URLs

These pages do not exist yet. Directory submissions that require them are blocked until they do. Do not invent stand-ins in the manifests.

- Documentation URL: none. `https://www.cybret.ai/docs` returned 404 on 2026-10-07, and `docs.cybret.ai` was not a live docs host in that review.
- Support URL: none. `https://www.cybret.ai/support` returned 404 on 2026-10-07. The privacy policy publishes `privacy@cybret.ai` for privacy requests. That is not a support page.

When those URLs exist, add them to the Claude manifest (`documentationUrl`, `supportUrl`) and the OpenAI interface (`supportURL`), and link them from this section.

## Layout

| Path | Role |
| --- | --- |
| `mcp.json` | Shared server config (Agent Plugins schema, `streamable-http`). |
| `.mcp.json` | Claude Code and Codex compatibility config (`type` `http`, same URL). |
| `plugin.json` | Portable Agent Plugins manifest, including OpenAI listing fields. |
| `.cursor-plugin/plugin.json` | Cursor plugin. |
| `.claude-plugin/plugin.json` | Claude Code plugin. |
| `.claude-plugin/marketplace.json` | Claude Code marketplace (`cybret`). |
| `.codex-plugin/plugin.json` | Codex compatibility manifest. |
| `server.json` | MCP Registry document for remote server `ai.cybret/findings`. Not published from this repo. |
| `skills/triage-cybret-findings/SKILL.md` | Client-neutral triage skill. |
| `LAUNCH.md` | Remaining submission steps and server-side blockers. |

The square icon is the official favicon from `https://www.cybret.ai/favicon.png`. See the pull request notes for which sizes are derived.

## License

[MIT](LICENSE). Copyright (c) 2026 Cybret.
