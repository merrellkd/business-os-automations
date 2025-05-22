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

    archive >> commit
    commit >> create_folder                 # default path covers 'no_changes'
    commit - "no_changes" >> create_folder
    commit - "committed" >> pr
    pr >> create_folder
    create_folder >> create_file

    return Flow(start=archive)
