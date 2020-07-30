import shutil
import tempfile
from pathlib import Path

from new_app.app.src import sync, determine_actions, FakeFileSystem


def test_when_a_file_exists_in_the_source_but_not_the_destination():
    source = {'sha1': 'my-file'}
    dest= {}
    filesystem = FakeFileSystem()

    reader = {'/srouce': source, '/dest': dest}

    synchronise_dirs(reader.pop, filesystem, "/source", "/dest")

    assert filesystem ==[("COPY", "/source/my-file", "/dest/my-file")]

def test_when_a_file_has_been_renamed_in_the_source():
    source = {'sha1': 'renamed-file'}
    dest = {'sha1': 'original-file'}
    filesystem = FakeFileSystem()

    reader = {'/srouce': source, '/dest': dest}

    synchronise_dirs(reader.pop, filesystem, "/source", "/dest")

    assert filesystem == [("MOVE", "/dest/original-file", "/dest/renamed-file")]

def test_when_a_file_exists_in_the_source_but_not_the_destination():
    try:
        source = tempfile.mkdtemp()
        dest = tempfile.mkdtemp()

        content = "I am a very useful file"
        (Path(source) / 'my-file').write_text(content)

        sync(source, dest)

        expected_path = Path(dest) / 'my-file'
        assert expected_path.exists()
        assert expected_path.read_text() == content
    finally:
        shutil.rmtree(source)
        shutil.rmtree(dest)


def test_when_a_file_has_been_renamed_in_the_source():
    try:
        source = tempfile.mkdtemp()
        dest = tempfile.mkdtemp()

        content = "I am a very useful file"
        source_path = Path(source) / 'source-filename'
        old_dest_path = Path(dest) / 'dest-filename'
        expected_dest_path = Path(dest) / 'source-filename'
        source_path.write_text(content)
        old_dest_path.write_text(content)
        sync(source, dest)
        assert old_dest_path.exists() is False
        assert expected_dest_path.read_text() == content

    finally:
        shutil.rmtree(source)
        shutil.rmtree(dest)


def test_when_a_file_exists_in_the_source_but_not_the_destination2():
    src_hashes = {'hash1': 'fn1'}
    dst_hashes = {}

    actions = determine_actions(src_hashes, dst_hashes, Path('/src'), Path('/dst'))

    assert list(actions) == [('copy', Path('/src/fn1'), Path('/dst/fn1'))]


def test_when_a_file_has_been_renamed_in_the_source2():
    src_hashes = {'hash1': 'fn1'}
    dst_hashes = {'hash1': 'fn2'}

    actions = determine_actions(src_hashes, dst_hashes, Path('/src'), Path('/dst'))

    assert list(actions) == [('move', Path('/dst/fn2'), Path('/dst/fn1'))]