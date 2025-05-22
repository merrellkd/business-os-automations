from pathlib import Path
from journal_daily_setup.flow import create_journal_flow


def main(journal_root: str = '00_daily-journal'):
    shared = {
        'journal_root': journal_root,
        'today_folder': '',
        'today_path': '',
        'enable_git': True
    }
    flow = create_journal_flow()
    flow.run(shared)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Daily journal setup')
    parser.add_argument('--root', default='00_daily-journal', help='Path to journal root')
    args = parser.parse_args()
    main(args.root)
