# FR-0001 — Constitutional Release Process Failures

## Status

Contained and verified through PR #7, main CI run #12, and release `constitution-v1.0-a0001`.

## Context

Repository: `AgentiCubed/agenticubed`

Workstream: publication of Constitution v1.0 and Amendment A-0001

Relevant artifacts:

- Constitution v1.0
- PR #7
- merge commit `e31c44460f2d6416cb2c2b4398c6b3a658147f29`
- release `constitution-v1.0-a0001`

## Observed Failures

### F1 — Governance files were committed directly to `main`

The initial Constitution, Ratification Record, Commentary, and amendment procedure were created through GitHub's web editor and committed directly to `main` instead of entering through a feature branch and pull request.

### F2 — Branch and commit context were repeatedly confused

GitHub pages showed a branch, a commit snapshot, or `main` in visually similar selectors. Attempts to edit RR-0001 were blocked when the page was on historical commit `a0cb786` rather than an editable branch.

### F3 — Required artifacts were believed to exist before verification

Conversation repeatedly treated four governance files as present before repository evidence confirmed their exact paths and contents.

### F4 — Ratification status contradicted itself

Amendment A-0001 stated `Ratified`, while RR-0001 stated that A-0001 remained proposed and that no amendment had been adopted.

### F5 — PR metadata was truncated and drifted

The PR description was accidentally reduced to its opening section during an automated update. It also named the DR path incorrectly and claimed `No constitutional authority changes`, although A-0001 changed constitutional wording without expanding authority.

### F6 — The first merge attempt used a prohibited method

The repository rejected a merge-commit attempt with HTTP 405 because merge commits were disabled. Squash merge was then used successfully.

### F7 — Workflow run number and PR number were confused

Main CI run `#12` was initially questioned because the merged pull request was `#7`. The identifiers belonged to different GitHub number spaces.

### F8 — Tag and release creation were not understood as one GitHub flow

The tag name was known, but the GitHub Release interface's `Choose a tag` field and tag-creation behavior were not understood until guided interactively.

### F9 — Reviews were not always context-complete

Claude could not access the private repository, and Copilot exhausted quota. Their assignments could not be completed because the exact files were not embedded in the review package and tool access was assumed.

### F10 — Claims of completion preceded Git evidence

Several assistant messages described branches, files, commits, or completion states that had not yet been verified. Later GitHub evidence corrected those claims.

## Expected Behavior

- Issue before implementation.
- Verified repository and branch before editing.
- Context-complete review packets.
- Exact file paths and contents confirmed from Git.
- PR diff and CI reviewed before merge.
- Main verified before tag.
- Tag and release published only after explicit authorization.
- No completion claim without repository evidence.

## Evidence

- Git commit history for the four direct-to-main governance commits.
- PR #7 commit and file history.
- PR #7 conversation showing metadata correction.
- Merge API rejection for merge commits and successful squash merge.
- Main CI run #12.
- Release `constitution-v1.0-a0001`.
- Conversation screenshots showing branch, commit, and file-path confusion.

## Impact

- Increased human attention and elapsed time.
- Risk of tagging an internally inconsistent constitutional state.
- Risk of duplicate or misplaced records.
- Risk of treating conversational memory as repository truth.
- Reduced confidence in completion claims until independently verified.

No product runtime, secret, `.env`, Dockerfile, generated file, or Cockpit change occurred.

## Immediate Corrections

- Created corrective branch `governance/constitution-v1.0-fix`.
- Added A-0001 and aligned Commentary, DR-0001, and RR-0001.
- Opened and reviewed PR #7.
- Corrected PR metadata.
- Waited for PR and main CI.
- Used squash merge after repository policy rejected merge commits.
- Published a release tied to the verified main state.

## Verification

- PR #7 merged successfully.
- Main commit `e31c44460f2d6416cb2c2b4398c6b3a658147f29` contains only the authorized governance changes.
- Main CI completed successfully.
- Release `constitution-v1.0-a0001` was published.

## Unresolved Facts

- The exact point at which each misunderstanding entered the process was not timestamped independently of conversation history.
- The repository does not yet enforce issue-first or PR-first governance mechanically.
- The optimal level of UI guidance versus command-line automation remains undecided.

## Linked Records

- [RM-0001](./RM-0001-constitutional-release-process.md)
- [IER-0001](./IER-0001-constitutional-baseline.md)
- [RL-0001](./RL-0001-failure-first-memory.md)
- Issue #8
- PR #7
- Release `constitution-v1.0-a0001`