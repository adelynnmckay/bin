import json
import sys
import pytest
from io import StringIO
from unittest.mock import patch
from src.fs import FileSystem, CLI

def test_cli_parse_getopts_style_args(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog", "realpath", "tests"])
    cli = CLI(FileSystem)
    args = cli.parse_args()
    assert args["command"] == "realpath"
    assert args["args"] == ["tests"]

def test_cli_parse_json_provided_as_arg(monkeypatch):
    test_input = json.dumps({"realpath": {"path": "tests"}})
    monkeypatch.setattr(sys, "argv", ["prog", test_input])
    cli = CLI(FileSystem)
    args = cli.parse_args()
    assert "realpath" in args

def test_cli_parse_json_stdin(monkeypatch):
    json_input = json.dumps({"realpath": {"path": "tests"}})
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(sys.stdin, "read", lambda: json_input)
    cli = CLI(FileSystem)
    args = cli.parse_args()
    assert "realpath" in args

def test_cli_eval_args_json(monkeypatch):
    json_input = json.dumps({"realpath": {"path": "."}})
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(sys.stdin, "read", lambda: json_input)
    cli = CLI(FileSystem)
    with patch.object(FileSystem, 'realpath', return_value=".") as mock_realpath:
        cli.eval_args()
        mock_realpath.assert_called()
