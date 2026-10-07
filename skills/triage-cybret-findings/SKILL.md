---
name: triage-cybret-findings
description: >
  Triage open Cybret security findings in the current repo. Use when the user
  asks to review, fix, or close Cybret findings, validated API or app
  vulnerabilities, or issues from the Cybret MCP server.
---

# Triage Cybret findings

Move an open Cybret finding into a fix in this repository, then record that status. Cybret findings are validated: the product has already confirmed the issue, so treat the tool result as the defect, not as unscored scanner noise. This server does not start scans. It lists findings, explains one finding, and updates status.

The steps are the same in Cursor, Claude Code, Codex, and any other client that can call the Cybret MCP tools.

## Preconditions

- The Cybret server at `https://mcp.cybret.ai/mcp` is connected, and the user has finished OAuth or configured an agent token.
- `list_open_findings` and `get_finding` require scope `findings:read`. `mark_status` requires scope `findings:write`. If a call is rejected for authorization, stop and name the missing scope. Do not ask the user to paste a token into the chat.
- Read each tool's live input schema from the MCP session before the first call. The names in this skill are the server's tools. Argument names and status enums must come from that live schema. Do not guess a parameter that the schema does not list.

## Steps

1. Call `list_open_findings`. The server returns the open findings for the credential's tenant. The 2026-10-07 server review found no severity, repository, or pagination arguments, so filter and sort on the client. If the result is an empty list, stop. Tell the user this credential has no open findings, and that findings show up after a scan at https://app.cybret.ai. Do not invent findings.

2. Rank what came back by severity, using the severity field in the payload. Recommend one finding, prefer one that maps to code in this repository, and continue with the finding the user picks. If they already named one, use that.

3. Call `get_finding` for that finding. Take the identifier from the list result and match it to the live schema. Summarize the validated issue, where it is, and the remediation guidance in the tool result. Do not replace that guidance with a generic write-up of the vulnerability class.

4. Implement the fix in this repository. Keep the diff limited to the finding. Follow the surrounding code. Add or adjust a test when the project already has a place for one. Do not weaken a control only to make the finding disappear.

5. Open a pull request, or name the branch the user is already reviewing, and put the Cybret finding identifier in the pull request body. If this session cannot open a pull request, give the user the title, the body, and the commit that contains the fix.

6. After the user confirms the fix is on a pull request, call `mark_status`. Use a status the user confirms and that the live schema allows. If the schema has a field for a pull request URL, pass the URL. The server review describes that link field, but the live schema wins if the name differs. Do not mark a finding resolved before the fix exists. If the tool result contains an error payload, treat that as failure and show it. Do not claim the status changed.

## Stop

- The server is not authenticated.
- The finding does not match code in this workspace. Say so and leave the status unchanged.
- The remediation needs a product decision you cannot infer. Ask once, then stop.
- The credential does not include `findings:write`. Leave the finding open and tell the user to reconnect and approve write access, or to use an agent token that includes `findings:write`.
