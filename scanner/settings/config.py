import os

import yaml

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

CONFIG = {}


def from_file(file_obj):
    CONFIG.update(yaml.load(file_obj, Loader=yaml.FullLoader))


if not CONFIG:
    # from_file(open(os.environ['SCANNER_CONFIG']))
    config_path = os.path.join(BASE_DIR, 'settings/config.yaml')
    from_file(open(config_path))

