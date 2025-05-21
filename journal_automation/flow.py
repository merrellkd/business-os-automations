from pocketflow import Flow
from journal_automation.nodes import ArchiveOldFolders, CreateTodayFolder, CreateJournalFile


def create_journal_flow():
    archive = ArchiveOldFolders()
    create_folder = CreateTodayFolder()
    create_file = CreateJournalFile()

    archive >> create_folder >> create_file

    return Flow(start=archive)
