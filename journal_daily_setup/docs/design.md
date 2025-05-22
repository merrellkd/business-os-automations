# Journal Automation Design

This project uses **PocketFlow** to automate creation of the daily journal folder.

## Flow Overview

```mermaid
flowchart LR
    A[ArchiveOldFolders] --> B[CreateTodayFolder]
    B --> C[CreateJournalFile]
```

1. **ArchiveOldFolders** – Move any existing date folders in `00_daily-journal` to the `archive/` hierarchy.
2. **CreateTodayFolder** – Create today's folder using the pattern `YYYY-MM-DD-<day>`.
3. **CreateJournalFile** – Place the journal template inside the new folder.

The automation should be triggered daily via the macOS launchd facilty.

Running the script manually is also safe; it will not overwrite existing folders or files.
