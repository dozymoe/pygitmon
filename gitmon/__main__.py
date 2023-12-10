import argparse
import logging
import os
from pathlib import Path
#-
from .tool import process_work_subject

def load_work_file(work_file):
    with work_file.open('r', encoding='utf-8') as f:
        if work_file.suffix in ('.yml', '.yaml'):
            import yaml
            return yaml.safe_load(f)
        elif work_file.suffix == '.json':
            import json
            return json.load(f)

    raise RuntimeError(f"Invalid git monitor file: {work_file}")


def main(args):
    logger = logging.getLogger(__name__)

    work_file = args.work_file or os.environ.get('GIT_MONITOR_FILE')
    if not work_file:
        logger.error("Working configuration file is required")
        return 1
    work_file = Path(work_file)
    if not work_file.exists():
        logger.error("File not found: %s", work_file)
        return 1

    ret = 0
    for work_subject in load_work_file(work_file):
        try:
            process_work_subject(work_subject)
        except:
            logger.exception("Problem updating workspace")
            ret += 1
    return ret


def command_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('work_file', nargs='?')
    parser.add_argument('-l', '--loglevel', action='store', default='info',
            choices=['debug', 'info', 'warning', 'error'])
    return parser.parse_args()


if __name__ == '__main__':
    args = command_args()
    logging.basicConfig(level=getattr(logging, args.loglevel.upper()))
    exit(main(args))
