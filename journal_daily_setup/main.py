from pathlib import Path
import logging
from journal_daily_setup.flow import create_journal_flow


def main(journal_root: str = '00_daily-journal', log_level: str = 'INFO'):
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    repo_root = Path(journal_root).parent
    shared = {
        'journal_root': journal_root,
        'today_folder': '',
        'today_path': '',
        'enable_git': True,
        'repo_root': repo_root,
    }
    flow = create_journal_flow()
    flow.run(shared)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Daily journal setup')
    parser.add_argument('--root', default='00_daily-journal', help='Path to journal root')
    parser.add_argument('--log-level', default='INFO', help='Logging level (e.g. DEBUG)')
    args = parser.parse_args()
    main(args.root, args.log_level)
