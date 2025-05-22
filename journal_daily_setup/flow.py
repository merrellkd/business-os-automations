from pocketflow import Flow
from journal_daily_setup.nodes import (
    ArchiveOldFolders,
    CreateTodayFolder,
    CreateJournalFile,
    CommitChanges,
    CreatePullRequest,
)


def create_journal_flow():
    archive = ArchiveOldFolders()
    create_folder = CreateTodayFolder()
    create_file = CreateJournalFile()
    commit_changes = CommitChanges()
    open_pr = CreatePullRequest()

    archive >> create_folder >> create_file >> commit_changes >> open_pr

    return Flow(start=archive)
