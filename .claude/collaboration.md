# Working With a Non-Technical Owner

Binding in `owner` mode (see `project.md`). In `developer` mode §2, §6 and
§7 are recommendations and the developer decides how to release.

The owner defines **what** the product does. They do not read code, do not
open a terminal and do not review diffs. Their one interface is GitHub:
the pull request, its green or red check, the Merge button, and the
Actions tab. A mentor reviews architecture and risky changes. Claude is
the only developer in the loop most of the time, so the rules below
replace the review a colleague would otherwise give.

## 1. Language

- Talk to the owner in the owner's language. Match their register.
- Code, comments, commit messages, `DECISIONS.md`, `requirements/` and
  everything in `.claude/` stay in English (`CLAUDE.md` Rule 1).
- No jargon in owner-facing text, including the PR description. If a
  technical term is unavoidable, explain it in half a sentence.

## 2. Nothing is built before it is written down

Every request that changes behaviour goes through `.claude/requirements.md`
first: Claude drafts the requirement, reads it back in plain language, the
owner confirms, then code is written. Exceptions that may skip the gate:

- Typos and wording changes in `strings.py` or templates
- A crash or wrong output where the correct behaviour is already defined
  in an approved requirement or a decision

If Claude is unsure whether something is an exception, it is not.

## 3. Ask before, not after

Ask the owner (and point them to the mentor when in doubt) before:

- Deleting or rewriting stored data, or a migration that can lose data
- Removing or hiding an existing feature
- Adding an external service, paid API, or anything with running costs
- Adding a dependency with a non-permissive licence
- Changing `docker-compose.yml`, workflows or anything under `.github/`
- Anything a `FINAL` decision in `DECISIONS.md` or
  `.claude/template-decisions.md` forbids
- Anything not covered by an approved requirement

Everything else that is reversible and inside the approved requirement:
just do it and report.

## 4. Never

- Never weaken, skip, delete or mark-xfail a test to make the suite green.
  A failing test is either a bug in the code or a requirement change;
  both go back to the owner. (Generalised from ZenTallyBot D-004.)
- Never merge to `main` and never push to it. Claude works on a feature
  branch and opens a pull request; the owner merges it on GitHub.
- Never tell the owner to run a command in a terminal. If something needs
  a terminal, it is the mentor's job (`.claude/operations.md`).
- Never modify `CLAUDE.md`.
- Never invent domain facts (prices, rules, thresholds, wording of the
  business). Ask, or leave a clearly marked placeholder.
- Never widen scope. A "while I'm at it" is a new requirement.
- Never claim something is tested, deployed or working without having run
  the command that proves it, or having seen the check on GitHub.

## 5. Disagree out loud

`CLAUDE.md` Rule 12 applies to the owner as well. When a request
contradicts an approved requirement, a `FINAL` decision, or
`.claude/architecture.md`: say so in one or two sentences, propose the
nearest thing that fits, and if the owner insists, log the conflict as a
Roadmap entry for the mentor rather than silently complying.

## 6. Delivering a change

1. Work on a branch named `claude/<req-id>-<slug>`.
2. Push and open a pull request using `.github/pull_request_template.md`.
   The "What changes for users" section is written for the owner.
3. Wait for the `Tests` check. Red: fix and push again; never ask the
   owner to merge a red PR.
4. Tell the owner, in their language, in this order:
   - **What changes for you** — one to three sentences, user perspective.
   - **What is still open** — including anything you decided not to do and why.
   - **What you need from me** — usually: "Review the description and
     press Merge on <PR link>. The server then tests and deploys on its
     own; the Actions tab shows green when it is live."
   No percentages, no "almost done".

## 7. Definition of done, for the owner

A change is done when all of these are true:

- The acceptance criteria of the requirement are covered by tests and the
  `Tests` check on the PR is green.
- `RELEASE_NOTES.md` has an entry if the owner would notice the change.
- `DECISIONS.md` has an entry if a way of doing things was chosen.
- The pull request is merged and the `Deploy` workflow is green.
- The requirement file says `IMPLEMENTED` with the version.
