from pocketflow import Flow
from journal_daily_setup.nodes import (
    ArchiveOldFolders,
    CommitChanges,
    CreatePullRequest,
    CreateTodayFolder,
    CreateJournalFile,
)


def create_journal_flow():
    archive = ArchiveOldFolders()
    commit = CommitChanges()
    pr = CreatePullRequest()
    create_folder = CreateTodayFolder()
    create_file = CreateJournalFile()

    archive >> commit >> pr >> create_folder >> create_file

    return Flow(start=archive)
