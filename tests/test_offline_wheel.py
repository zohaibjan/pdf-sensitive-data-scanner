from pathlib import Path
import zipfile


def test_bundled_application_wheel_matches_current_python_source():
    root=Path(__file__).resolve().parents[1]
    wheel=root/'offline/wheels/file_flag-0.1.1-py3-none-any.whl'
    assert wheel.is_file(), 'Rebuild the application wheel after source changes'
    with zipfile.ZipFile(wheel) as archive:
        for source in (root/'src/file_flag').rglob('*.py'):
            name=source.relative_to(root/'src').as_posix()
            assert archive.read(name)==source.read_bytes(), f'Stale offline wheel: {name}'
