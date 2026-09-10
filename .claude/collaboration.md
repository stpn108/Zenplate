# Working With a Non-Technical Owner

The owner of this project defines **what** the product does. They do not
read code, do not run tests by hand and do not review diffs. A mentor
reviews architecture and risky changes, but not every change. Claude is
the only developer in the loop most of the time, so the rules below replace
the review a colleague would otherwise give.

## 1. Language

- Talk to the owner in the owner's language. Match their register.
- Code, comments, commit messages, `DECISIONS.md`, `requirements/` and
  everything in `.claude/` stay in English (`CLAUDE.md` Rule 1).
- No jargon in owner-facing text. If a technical term is unavoidable,
  explain it in half a sentence the first time.

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
- Anything a `FINAL` decision in `DECISIONS.md` forbids
- Anything not covered by an approved requirement

Everything else that is reversible and inside the approved requirement:
just do it and report.

## 4. Never

- Never weaken, skip, delete or mark-xfail a test to make the suite green.
  A failing test is either a bug in the code or a requirement change;
  both go back to the owner. (Generalised from ZenTallyBot D-004.)
- Never merge to `main`. Claude works on a feature branch; the owner
  releases with `./merge-to-main.sh`. Pull requests are optional and used
  when the mentor wants to review.
- Never modify `CLAUDE.md`.
- Never invent domain facts (prices, rules, thresholds, wording of the
  business). Ask, or leave a clearly marked placeholder.
- Never widen scope. A "while I'm at it" is a new requirement.
- Never claim something is tested, deployed or working without having run
  the command that proves it.

## 5. Disagree out loud

`CLAUDE.md` Rule 12 applies to the owner as well. When a request
contradicts an approved requirement, a `FINAL` decision, or
`.claude/architecture.md`: say so in one or two sentences, propose the
nearest thing that fits, and if the owner insists, log the conflict as a
Roadmap entry for the mentor rather than silently complying.

## 6. Reporting

After each unit of work tell the owner, in this order and in their language:

1. **What changed for you** — one to three sentences, user perspective.
2. **What is still open** — including anything you decided not to do and why.
3. **What you need from me** — questions, confirmations, or "nothing".

No percentages, no "almost done". Something is done when
`.claude/checklist.md` is fully ticked; otherwise it is open.

## 7. Definition of done, for the owner

A change is done when all of these are true:

- The acceptance criteria of the requirement are covered by tests and
  `pytest` is green.
- `RELEASE_NOTES.md` has an entry if the owner would notice the change.
- `DECISIONS.md` has an entry if a way of doing things was chosen.
- The work is on a feature branch and pushed.
- After `./merge-to-main.sh`, the deploy pipeline is green and
  `./version.sh` shows the new version.
