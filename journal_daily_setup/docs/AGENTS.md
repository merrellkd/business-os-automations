## PocketFlow

- I am using pocketflow for its simplicity and elegance in specifying workflows.
- I am trying to increase my understanding and proficiency with pocketflow as a way to build skills and expand effectiveness of agentic coding practices.

## Coding Instructions

- Insert comments liberally.
- Comments should be geared towards teaching the concepts of Python and PocketFlow

## Journal Folder Structure Schema

Daily journaling system with a well-defined hierarchical organization:

```
00_daily-journal/
├── [CURRENT-DATE-FOLDER]/    # Current day's entries
│   └── [DATE].journal.md     # Main journal file for current day
└── archive/                  # Historical entries
    └── [YEAR]/               # Year-level organization
        └── [MONTH-CODE]-[MONTH-NAME]/  # Month-level organization
            └── [YYYY-MM-DD-DAY]/       # Day-level folders
                ├── [YYYY-MM-DD-DAY].journal.md  # Main journal file
                └── [ADDITIONAL-FILES].md        # Supporting documents
```

### Key Schema Characteristics:

1. **Top-level organization**:

   - `00_daily-journal/` serves as the root directory
   - Current day's entries are stored directly under the root
   - All past entries are stored in an `archive/` subdirectory

2. **Date-based hierarchical structure**:

   - Year folders (e.g., `2025/`)
   - Month folders with numeric prefix and name (e.g., `05-may/`)
   - Day folders with ISO-style date and weekday suffix (e.g., `2025-05-20-tue/`)

3. **File naming conventions**:

   - Main journal files follow pattern: `YYYY-MM-DD-DAY.journal.md`
   - Additional content files use descriptive names with `.md` extension
   - Occasional non-markdown files (images, text files) are included

4. **Special files**:

   - `evening-review-output.md` appears regularly, suggesting automated processing
   - Various perspective files (e.g., `[NAME].perspective.md`)
   - Meeting notes and topic-specific documents

5. **Template for daily `.journa.md` file**

```
# [YYYY-MM-DD-DAY].journal.md

## Today's Priorities

### - 1)

### - 2)

### - 3)

## Daily Review & Reflections
```

This schema supports a daily journaling practice with:

- Main journal entries (`.journal.md` files)
- Supporting notes and documents
- Regular review outputs (likely automated)
- Topic-based content organized by date

### Technical requirements for Python automation:

1. The automation should maintain this hierarchical structure
2. It should handle date transitions, moving today's entries to archive at day end
3. It should create new day folders with proper naming conventions
4. It should support both regular journal files and special document types
5. It should manage file paths that follow the established pattern

This structured approach allows for efficient organization, retrieval, and processing of daily journal entries across time.
