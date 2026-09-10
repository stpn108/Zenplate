---
name: onboarding
description: First-session interview for a new project built from Zenplate. Fills .claude/project.md, .claude/glossary.md and the first requirement from the owner's answers. Use when project.md still contains <PROJECT_NAME> placeholders, or when the owner asks to set up, start or initialise the project.
---

# Project onboarding

You are talking to the project owner, who is not a developer. Ask in their
language, one topic at a time, in plain words. Write the results in
English into the files below. Do not write code in this session.

## 1. Before asking anything

Read `.claude/project.md`, `.claude/collaboration.md`,
`.claude/requirements.md`, `.claude/glossary.md`. Check `git log` to see
whether this is a fresh template. If `project.md` has no placeholders
left, stop and tell the owner onboarding was already done.

## 2. Interview

Ask these, in order, and wait for each answer. Reflect the answer back in
one sentence before moving on.

1. **What is it?** "Describe in two or three sentences what this thing
   should do for whom." → `project.md` description.
2. **What is it not?** "What might people expect from it that you
   explicitly do not want to build, at least for now?" Push for three
   items. → `project.md` "What this project is NOT".
3. **Who is involved?** Owner name, mentor name and how to reach them.
   → `project.md` "People".
4. **Words.** "Which words do you use for the main things in it? For
   each: what exactly does it mean, and what is it not?" Aim for five to
   ten terms. Ask for units where numbers are involved. → `glossary.md`.
5. **Channel and stack.** "How do users reach it: chat bot, website,
   e-mail, something else?" Map to the stack section; only tick optional
   components the owner named. → `project.md` "Stack".
6. **The first thing.** "If only one thing worked next week, what should
   it be?" → draft `requirements/REQ-001-<slug>.md` from
   `requirements/TEMPLATE.md`, with the owner's words verbatim under
   "Owner ask".
7. **The number.** "How will you know it works? What would you look at?"
   → success metric of REQ-001, and a note in `project.md` if it is a
   project-wide KPI.

## 3. Write

- Replace every `<placeholder>` in `.claude/project.md`.
- Fill the glossary table; one row per term, code names in `snake_case`
  derived from the English meaning.
- Save REQ-001 with status `DRAFT`.
- Set `RELEASE_NOTES.md` v0.1 date to today.

## 4. Read back

Summarise in the owner's language, under ten sentences: what the project
is, what it is not, the first requirement and its acceptance criteria.
Ask for an explicit yes. On yes, set REQ-001 to `APPROVED` and tell the
owner that implementation can start in the next session.

## 5. Do not

- Do not invent terms, thresholds or features the owner did not name.
- Do not skip the "what it is NOT" question; it is the cheapest scope
  guard the project will ever get.
- Do not start implementing in the same session.
