"""Node submission review queue: normalize, dedupe, note handling."""
import os

os.environ["HELIX_SUBMISSIONS_FILE"] = "/tmp/test_submissions.json"

from node import submissions


def setup_function(_):
    submissions._write([])


def test_add_and_normalize():
    assert submissions.add_submission("your-node.example.com:8000") == "http://your-node.example.com:8000"
    queue = submissions.get_submissions()
    assert len(queue) == 1
    assert queue[0]["url"] == "http://your-node.example.com:8000"
    assert "at" in queue[0]


def test_dedupe():
    submissions.add_submission("https://a.example.com")
    submissions.add_submission("https://a.example.com/")   # trailing slash normalizes the same
    assert len(submissions.get_submissions()) == 1


def test_invalid_rejected():
    assert submissions.add_submission("") is None
    assert submissions.get_submissions() == []


def test_note_is_kept_and_capped():
    submissions.add_submission("https://b.example.com", note="x" * 400)
    entry = submissions.get_submissions()[0]
    assert entry["note"] == "x" * 280
