---
agent: agent
description: Create a durable Fux spec and task plan for a requested change.
---

Plan `${input:request}` using Fux.

1. Confirm the repository has `.fux/`; run `fux init` if it does not.
2. Run `fux build` so INDEX and graph data are fresh.
3. Create a spec entry with `fux new spec <kebab-id>`.
4. Fill requirements as user stories plus EARS acceptance criteria.
5. Identify real affected files with `fux refs <path>` and graph/INDEX reads.
6. Create task entries with `fux new task <kebab-id>`, linking each task to the spec.
7. Do not create orphan planning docs when the information belongs in `.fux/`.
