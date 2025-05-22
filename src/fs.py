#!/usr/bin/env python3

import os
import sys
import json
import re
import shutil
import subprocess
import concurrent.futures
import argparse
import logging
from functools import partial
from typing import Callable, Any

def setup_logging():
    logger_name = os.path.basename(sys.argv[0]).split('.')[0]
    log_format = f'{logger_name} %(asctime)s %(levelname)s: %(message)s'
    log_colors = {
        "INFO": "\033[92m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
        "RESET": "\033[0m"
    }

    class ColorFormatter(logging.Formatter):
        def format(self, record):
            color = log_colors.get(record.levelname, "")
            reset = log_colors["RESET"]
            record.msg = f"{color}{record.msg}{reset}"
            return super().format(record)

    logger = logging.getLogger(logger_name)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColorFormatter(log_format))
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger

logger = setup_logging()

class FileSystem:

    class Enforce:
        def __init__(self, path):
            self._path = path
            self._abspath = os.path.abspath(path)

        def isabs(self):
            if not os.path.isabs(self._path):
                raise ValueError(f"{self._path} is not an absolute path")
            return self

        def exists(self):
            self.isabs()
            if not os.path.exists(self._path):
                raise FileNotFoundError(f"{self._path} does not exist")
            return self

        def notexists(self):
            self.isabs()
            if os.path.exists(self._path):
                raise FileExistsError(f"{self._path} already exists")
            return self

        def isdir(self):
            self.isabs()
            if not os.path.isdir(self._path):
                raise ValueError(f"{self._path} is not a directory")
            return self

        def isnotdir(self):
            self.isabs()
            if os.path.isdir(self._abspath):
                raise ValueError(f"{self._path} is a directory")

        def isfile(self):
            self.isabs()
            if not os.path.isfile(self._abspath):
                raise ValueError(f"{self._path} is not a regular file")
            return self

        def isnotfile(self):
            self.isabs()
            if os.path.isfile(self._path):
                raise ValueError(f"{self._path} is a regular file")
            return self

        def isfile_or_isdir(self):
            self.isabs()
            if not os.path.isfile(self._abspath) and not os.path.isdir(self._abspath):
                raise ValueError(f"{self._path} is not a regular file or a directory")
            return self

        def empty(self):
            self.isdir()
            if os.listdir(self._path):
                raise ValueError(f"{self._path} is not empty")
            return self

        def notempty(self):
            self.isdir()
            if not os.listdir(self._path):
                raise ValueError(f"{self._path} is empty")
            return self

    @classmethod
    def realpath(cls, *path, relative_to=None):
        def _realpath(p):
            return os.path.realpath(os.path.expanduser(os.path.expandvars(p)))
        if len(path) == 1:
            abs_path = _realpath(path[0])
            if relative_to is not None:
                return os.path.relpath(abs_path, _realpath(relative_to))
            return abs_path
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return list(executor.map(_realpath, path))

    @classmethod
    def ls(cls, *path):
        def _ls(p):
            abs_path = cls.realpath(p)
            enforce = cls.Enforce(abs_path)
            enforce.isfile_or_isdir()
            if os.path.isfile(abs_path):
                return [abs_path]
            return [os.path.join(abs_path, x) for x in os.listdir(abs_path)
                    if x not in ('.', '..')]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(_ls, path)
        return [item for sublist in results for item in sublist]

    @classmethod
    def rmdir(cls, *path, force=True):
        def _rmdir(p):
            abs_path = cls.realpath(p)
            if not os.path.exists(abs_path):
                return
            enforce = cls.Enforce(abs_path)
            enforce.isdir()
            if not force:
                enforce.empty()
            shutil.rmtree(abs_path)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(_rmdir, path)

    @classmethod
    def rm(cls, *path, recursive=True, force=True):
        def _rm(p):
            abs_path = cls.realpath(p)
            if not os.path.exists(abs_path):
                return
            enforce = cls.Enforce(abs_path)
            if not recursive:
                enforce.isfile()
            enforce.isfile_or_isdir()
            if os.path.isfile(abs_path):
                os.remove(abs_path)
            else:
                cls.rmdir(abs_path, force=force)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(_rm, path)

    @classmethod
    def cp(cls, source, destination, recursive=True, force=True, include=None, exclude=None):
        abs_src_path = cls.realpath(source)
        abs_dest_path = cls.realpath(destination)
        src_enforce = cls.Enforce(abs_src_path)
        src_enforce.exists()
        if not recursive:
            src_enforce.isfile()
        dest_enforce = cls.Enforce(abs_dest_path)
        if include or exclude:
            dest_enforce.isdir()
            inc = [include] if isinstance(include, str) else include or [".*"]
            exc = [exclude] if isinstance(exclude, str) else exclude or []
            inc_re = [re.compile(x) for x in inc]
            exc_re = [re.compile(x) for x in exc]
            is_included = lambda path: any(r.match(path) for r in inc_re)
            is_excluded = lambda path: any(r.match(path) for r in exc_re)

            rel_cp_paths = [os.path.relpath(x, abs_src_path) for x in cls.ls(abs_src_path)]
            abs_cp_paths = [(os.path.join(abs_src_path, x), os.path.join(abs_dest_path, x))
                            for x in rel_cp_paths if is_included(x) and not is_excluded(x)]
            rel_rm_paths = [os.path.relpath(x, abs_dest_path) for x in cls.ls(abs_dest_path)]
            abs_rm_paths = [os.path.join(abs_dest_path, x) for x in rel_rm_paths
                            if not is_excluded(x) and x not in rel_cp_paths]

            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(lambda p: cls.cp(*p, recursive=recursive, force=force), abs_cp_paths)
                executor.submit(cls.rm, *abs_rm_paths)
        else:
            if not force:
                dest_enforce.notexists()
            os.makedirs(os.path.dirname(abs_dest_path), exist_ok=True)
            if os.path.isfile(abs_src_path):
                cls.rm(abs_dest_path)
                subprocess.run(["rsync", "-a", f"{abs_src_path}", f"{abs_dest_path}"])
            elif os.path.isdir(abs_src_path):
                if os.path.isfile(abs_dest_path):
                    cls.rm(abs_dest_path)
                subprocess.run(["rsync", "-a", "--delete", f"{abs_src_path}/", f"{abs_dest_path}/"])
            else:
                dest_enforce.isfile_or_isdir()

class CLI:
    def __init__(self, cls: type):
        self._cls = cls

    def parse_getopts_style_args(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command", required=True)
        for name in dir(self._cls):
            method = getattr(self._cls, name)
            if callable(method) and not name.startswith('_'):
                subparsers.add_parser(name).add_argument("args", nargs='*')
        return parser.parse_args()

    def parse_json_passed_by_stdin(self):
        try:
            input_data = sys.stdin.read()
            if input_data.strip():
                return json.loads(input_data)
        except Exception as e:
            logger.warning(f"Failed to read JSON from stdin: {e}")
        return {}

    def parse_json_provided_as_arg(self):
        return json.loads(sys.argv[1])

    def parse_args(self):
        if not sys.stdin.isatty():
            return self.parse_json_passed_by_stdin()
        if len(sys.argv) > 1 and sys.argv[1].startswith('{'):
            return self.parse_json_provided_as_arg()
        return vars(self.parse_getopts_style_args())

    def eval_args(self):
        args = self.parse_args()
        if isinstance(args, dict) and "command" in args:
            cmd = args.pop("command")
            method = getattr(self._cls, cmd)
            method(*args.get("args", []))
        elif isinstance(args, dict):
            for cmd, kwargs in args.items():
                getattr(self._cls, cmd)(**kwargs)
        elif isinstance(args, list):
            for item in args:
                for cmd, kwargs in item.items():
                    getattr(self._cls, cmd)(**kwargs)

def main():
    CLI(FileSystem).eval_args()

if __name__ == "__main__":
    main()
