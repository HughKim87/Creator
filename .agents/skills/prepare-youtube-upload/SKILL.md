---
name: prepare-youtube-upload
description: Prepare and validate a complete manual YouTube upload package containing the video, approved title and description, thumbnail, SRT captions, channel settings, and a copy-ready upload guide. Use when the user asks to prepare YouTube upload materials, assemble an upload package, or finish a video workflow without automating YouTube Studio.
---

# Prepare YouTube Upload

Prepare local upload materials for the user. Do not operate YouTube or a browser.

## Required input and output

Use one `youtube-manual-upload-v1` JSON package. Read [references/manual-upload-package-format.md](references/manual-upload-package-format.md) when creating or changing it.

Generate and validate the copy-ready guide:

```powershell
python scripts/prepare_upload_package.py <youtube-manual-upload.json>
```

The package may include `preparation.keep_files` for helper content such as a Markdown description. To remove intermediate files safely, preview the allowlist first:

```powershell
python scripts/retain_upload_package.py <youtube-manual-upload.json>
```

Use `--apply` only after the user explicitly authorizes cleanup. Never use a wildcard deletion in the output directory.

The command writes `YOUTUBE-MANUAL-UPLOAD.md` beside the package unless `--guide` specifies another path.

## Workflow

1. Resolve the video, thumbnail, SRT, and approved title-thumbnail package relative to the JSON package.
2. Confirm the title and thumbnail match the user-approved title-thumbnail package.
3. Store only the channel name. Do not store or validate a channel ID; the user confirms the destination channel directly in YouTube Studio during manual upload.
4. Validate the video extension and size, 1280×720 thumbnail and 2 MB limit, SRT timing structure, title length, description length, and manual settings.
5. Record an existing upload only as a duplicate warning. Never treat it as an instruction to update or replace that video.
6. Generate the Korean manual upload guide with absolute file paths, copy-ready title and description, settings, hashes, retention files, and ordered manual steps.
7. Re-read the generated guide and report the package, guide, video, thumbnail, SRT, description, and retention paths.

## Manual-only boundary

- Never open or control Chrome, YouTube Studio, or another browser.
- Never call a YouTube API, upload a file, save metadata, add captions, change visibility, publish, schedule, delete, or replace a video.
- Never verify whether the user uploaded, selected the intended channel, published, or changed visibility after handing off the guide.
- Never request browser login, profile access, cookies, passwords, or external-upload approval.
- Tell the user that all YouTube actions remain manual.
- Do not report the workflow complete until the local package and guide pass validation.
- Once the local package and guide pass validation, report the production workflow complete with no remaining agent action. Do not leave manual upload as a blocker or follow-up task.

## Completion criteria

- All four referenced artifacts exist and are non-empty.
- The title-thumbnail package is user-approved and matches the manual package.
- The generated guide contains the exact title, description, paths, channel name and Studio manual-confirmation instruction, and duplicate warning when applicable.
- The package and guide contain no channel ID or placeholder channel ID.
- The preparation script exits with `status: ready`, no errors, and no warnings other than an intentional existing-upload warning.
- Passing these criteria completes the entire agent-owned video production workflow.
