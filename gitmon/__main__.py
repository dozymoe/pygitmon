import logging
import os
from pathlib import Path
#-
from .tool import process_work_subject

WORK_FILE = Path(os.environ.get('GIT_MONITOR_FILE'))

def load_work_file(work_file):
    with work_file.open('r', encoding='utf-8') as f:
        if work_file.suffix in ('.yml', '.yaml'):
            import yaml
            return yaml.safe_load(f)
        elif work_file.suffix == '.json':
            import json
            return json.load(f)

    raise RuntimeError(f"Invalid git monitor file: {work_file}")


def main():
    work_file = Path(WORK_FILE)
    assert work_file.exists() == True

    logger = logging.getLogger(__name__)

    for work_subject in load_work_file(work_file):
        try:
            process_work_subject(work_subject)
        except:
            logger.exception("Problem updating workspace")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
