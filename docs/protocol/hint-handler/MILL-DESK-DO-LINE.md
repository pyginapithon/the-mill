# Proposed mill-desk awareness DO (do not apply to sand-data SoR yet)

**Target (when package lands):** `docs/protocol/skill.md` -> recopy to mill-desk `SKILL.md`.

**Living SoR for this draft:** `docs/protocol/hint-handler/` in the mill pack. The installed mill-desk `SKILL.md` is a copy - do not garden it unless it is the agreed living SoR.

## One-line DO (insert near connect pointer, ~line 14)

Current:

> Chat wins over HINT. mill connect foreground vs background: [connect.md](connect.md).

Proposed:

> Chat wins over HINT. mill connect foreground vs background: [connect.md](connect.md). **DO:** background HINTs -> load **hint-handler** after approve background.

## JOIN.md pointer (optional, one clause)

After the connect.md sentence in JOIN.md, add: `Background program playbook: protocol/hint-handler/SKILL.md` (once Builder lands the folder into the package).

## Why not patch installed skill now

- The installed pack's `docs/` is package-owned.
- Sanitize checkout lacks `connect.md` (incomplete host-agnostic tree).
- Loop-2/Builder must land `docs/protocol/hint-handler/` into the-mill package; then recopy skill.md -> mill-desk.
