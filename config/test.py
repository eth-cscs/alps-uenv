#!/usr/bin/env python3

import pathlib
import sys
import yaml

prefix = pathlib.Path(__file__).parent.resolve()
sys.path = [prefix.as_posix()] + sys.path

print(sys.path)

import schema

# required config.yaml file
config_path = prefix / "config.yaml"

with config_path.open() as fid:
    raw = yaml.load(fid, Loader=yaml.Loader)
    schema.config_validator.validate(raw)
    config = raw
