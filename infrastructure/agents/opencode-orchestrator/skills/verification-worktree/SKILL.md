---
name: verification-worktree
description: Run independent verification in a disposable worktree or sandbox so the main working tree is never modified.
---

# Verification worktree

Vouch must not change the main checkout. Use a disposable copy for every test run.

1. Create a worktree from the current `HEAD`:

   ```sh
   git worktree add /tmp/opencode/verify-<unique> HEAD
   ```

   If the `opencode` worktree tools are available, use `opencode worktree_create` instead.

2. Run tests, formatters, linters and integration checks inside that worktree. Install dependencies only there or in a disposable microsandbox.

3. Do not edit the main checkout. If a test requires a source change, report the required change; do not apply it.

4. Remove the worktree and any test services when finished:

   ```sh
   git worktree remove --force /tmp/opencode/verify-<unique>
   ```

5. If a worktree cannot be created, use a microsandbox copy. If neither is possible, stop and ask instead of running tests in the main tree.

A test that writes build artifacts inside its own worktree is fine. A test that modifies the main checkout is not verification.
