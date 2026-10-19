import json
from pathlib import Path
from file_flag.detectors.base import Finding
from file_flag.scanner import ScanResult
from file_flag.reporting import write_report


def test_masking_does_not_leak_adjacent_identifiers(tmp_path):
    finding = Finding(detector='tfn', kind='tfn', raw_value='123456782',
                      context='TFN 123456782, neighbour 987654321')
    result = ScanResult(path=Path('synthetic.pdf'), flagged=True, findings=[finding])
    output = tmp_path / 'report.json'
    write_report([result], output)
    text = output.read_text()
    assert '123456782' not in text and '987654321' not in text
    assert json.loads(text)['results'][0]['findings'][0]['context'] == '[REDACTED]'
    write_report([result], output, mask=False)
    assert '123456782' in output.read_text() and '987654321' in output.read_text()


def test_failed_files_remain_inspectable(tmp_path):
    result = ScanResult(path=Path('broken.pdf'), error='open failed')
    output = tmp_path / 'report.json'
    write_report([result], output)
    report = json.loads(output.read_text())
    assert report['summary']['flagged'] == 0
    assert report['summary']['errors'] == 1
    assert report['results'][0]['error'] == 'open failed'
