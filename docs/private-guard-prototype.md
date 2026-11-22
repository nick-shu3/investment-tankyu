# G03: Private publication guard — prototype

Status: **prototype / not a merge gate**. This is a generic implementation with synthetic tests. It does not register a GitHub App, create credentials, handle private real-world values, or change existing publication rules.

## Trust boundaries
- This scanner operates on the supplied Git commit by `git ls-tree` / `git cat-file`, without checking out or executing PR code, hooks, build tools or filters.
- `--policy` must refer to a private local JSON file **outside the repository and outside AI-accessible workspaces**. No real policy values belong in source, Issues, PR descriptions, fixtures, console output, or CI.
- Run in a separately isolated, network-blocked process. The process may read the policy but must **never** possess the dedicated GitHub App private key or installation token.
- Current CI runs **only synthetic unit tests**. Do not run the real private scanner in GitHub Actions.
- A future separately protected issuer will accept a validated commit identity and human approval, never raw PR code or the exclusion policy. GitHub checks and Ruleset enforcement remain **unimplemented**.

## Local interface
```text
python scripts/private_guard.py --repo /path/to/bare-repo --sha <full-commit-sha> --policy /private/path/policy.json
```
Expected private policy schema (illustrative placeholder values only):
```json
{"ids":["example-company"],"tickers":["7381"],"names":["架空デモ株式会社"]}
```
The scanner emits a generic PASS or FAIL and never the matching term. It exits nonzero when the policy is absent, malformed, empty, or a violation is detected.

## Limitations / fail-closed gates
- This prototype **does not** certify that the local process or secrets are isolated, prevent a compromised parser from faking a result, validate human approvals, implement an authenticated issuer, or block a GitHub merge. Those require G03 integration and on-device testing.
- It rejects symlinks, gitlinks, invalid encodings and some unsafe paths instead of dereferencing them. Binary images and embedded image text are not inspected; perform a separate unprivileged review.
- The free-text numeric matcher deliberately requires security-code context to avoid false positives on timestamps. Coverage and false-positive rates need further tests.
- Only the configured content extensions and path scopes are parsed. Scope changes require explicit review before using the guard as an enforcement gate.
- Strict merge synchronization, SHA freshness across merge/squash, expected check source, the separation of validation versus issuing, token minimization, local OS access controls and T01–T26 remain integration acceptance criteria.
- Never treat this branch, its tests, or its PR as proof that G03 is complete.

## Prerequisites for production
1. Complete G01 historical exposure decision and G02 local isolation decision, including Windows 11 Home support.
2. Create a private, repository-scoped dedicated GitHub App with minimal Checks permission and no administrative permissions.
3. Implement a separate human-mediated, passphrase-protected check issuer on the trusted personal device.
4. Configure and test the main Ruleset's required check source, direct-push blocking, and merge behaviors.
5. Run T01–T26 with dummy values in the actual host/sandbox configuration; measure review time and restore procedures.
6. Only then consider replacing any existing public-side exclusion logic.
