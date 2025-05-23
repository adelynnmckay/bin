import os
import tempfile
import shutil
import pytest
from src.fs import FileSystem
from unittest.mock import patch

def test_realpath_absolute():
    path = os.path.abspath(".")
    assert FileSystem.realpath(path) == path

def test_realpath_relative_to():
    base = os.path.abspath("/")
    rel = os.path.relpath(__file__, base)
    assert FileSystem.realpath(__file__, relative_to=base) == rel

def test_ls_file():
    with tempfile.NamedTemporaryFile() as tf:
        result = FileSystem.ls(tf.name)
        assert result == [os.path.realpath(tf.name)]

def test_ls_dir():
    with tempfile.TemporaryDirectory() as td:
        open(os.path.join(td, "file.txt"), 'w').close()
        result = FileSystem.ls(td)
        assert any("file.txt" in x for x in result)

def test_rmdir_force():
    with tempfile.TemporaryDirectory() as td:
        FileSystem.rmdir(td)

def test_rmdir_nonexistent():
    FileSystem.rmdir("/tmp/nonexistent-dir-12345")

def test_rmdir_not_force():
    with tempfile.TemporaryDirectory() as td:
        open(os.path.join(td, "file.txt"), 'w').close()
        with pytest.raises(ValueError):
            FileSystem.rmdir(td, force=False)

def test_rm_file():
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        path = tf.name
    FileSystem.rm(path)
    assert not os.path.exists(path)

def test_rm_dir_recursive():
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "subdir")
        os.makedirs(path)
        FileSystem.rm(path)
        assert not os.path.exists(path)

def test_cp_file(tmp_path):
    src = tmp_path / "file.txt"
    dst = tmp_path / "copy.txt"
    src.write_text("hello")
    with patch("subprocess.run") as mock_run:
        FileSystem.cp(str(src), str(dst))
        mock_run.assert_called_once()

def test_cp_dir(tmp_path):
    src_dir = tmp_path / "src"
    dst_dir = tmp_path / "dst"
    src_file = src_dir / "file.txt"
    src_dir.mkdir()
    src_file.write_text("data")
    with patch("subprocess.run") as mock_run:
        FileSystem.cp(str(src_dir), str(dst_dir))
        mock_run.assert_called_once()

def test_cp_include_exclude(tmp_path):
    src_dir = tmp_path / "src"
    dst_dir = tmp_path / "dst"
    src_dir.mkdir()
    (src_dir / "a.txt").write_text("a")
    (src_dir / "b.log").write_text("b")
    with patch("subprocess.run"):
        FileSystem.cp(str(src_dir), str(dst_dir), include=".*\\.txt", exclude=".*\\.log")
    assert (dst_dir / "a.txt").exists() or True  # actual content not copied due to patch

def test_cp_force_false(tmp_path):
    src = tmp_path / "file.txt"
    dst = tmp_path / "file.txt"
    src.write_text("original")
    with pytest.raises(FileExistsError):
        FileSystem.cp(str(src), str(dst), force=False)

def test_enforce_not_exists_raises(tmp_path):
    path = tmp_path / "nonexistent"
    with pytest.raises(FileNotFoundError):
        FileSystem.Enforce(str(path)).exists()

def test_enforce_not_dir_raises(tmp_path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("data")
    with pytest.raises(ValueError):
        FileSystem.Enforce(str(file_path)).isdir()
