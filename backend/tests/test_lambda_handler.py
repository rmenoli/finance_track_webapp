"""Tests for lambda_handler S3 sync functions."""

from unittest.mock import MagicMock, patch

import pytest


# We import the functions directly — NOT the module top-level,
# because module-level code runs migrations and downloads from S3.
# We patch before importing to prevent side effects.


@pytest.fixture(autouse=True)
def patch_module_level_side_effects():
    """Prevent cold-start side effects when importing lambda_handler in tests.

    Patches at the boto3/alembic level so they're active even on the very first
    import of lambda_handler (whose module-level code calls both).
    """
    with (
        patch("boto3.client"),
        patch("alembic.command.upgrade"),
    ):
        yield


def test_download_db_from_s3_success(tmp_path):
    """Downloads DB file from S3 to the local path."""
    from lambda_handler import _download_db_from_s3

    mock_s3 = MagicMock()
    with (
        patch("lambda_handler.boto3.client", return_value=mock_s3),
        patch("lambda_handler._DB_LOCAL_PATH", str(tmp_path / "portfolio.db")),
    ):
        _download_db_from_s3()

    mock_s3.download_file.assert_called_once()
    args = mock_s3.download_file.call_args[0]
    assert args[2] == str(tmp_path / "portfolio.db")


def test_download_db_from_s3_not_found_starts_fresh():
    """When S3 has no DB (404), function completes without error."""
    from lambda_handler import _download_db_from_s3

    mock_s3 = MagicMock()
    error_response = {"Error": {"Code": "404", "Message": "Not Found"}}
    mock_s3.download_file.side_effect = mock_s3.exceptions.ClientError(
        error_response, "GetObject"
    )
    mock_s3.exceptions.ClientError = type(
        "ClientError", (Exception,), {"response": error_response}
    )

    with patch("lambda_handler.boto3.client", return_value=mock_s3):
        # Should not raise
        _download_db_from_s3()


def test_download_db_from_s3_other_error_raises():
    """Non-404 S3 errors are re-raised."""
    from lambda_handler import _download_db_from_s3

    mock_s3 = MagicMock()

    class ClientError(Exception):
        def __init__(self):
            self.response = {"Error": {"Code": "403", "Message": "Forbidden"}}

    mock_s3.download_file.side_effect = ClientError()
    mock_s3.exceptions.ClientError = ClientError

    with patch("lambda_handler.boto3.client", return_value=mock_s3):
        with pytest.raises(ClientError):
            _download_db_from_s3()


def test_upload_db_to_s3(tmp_path):
    """Uploads the local DB file to S3."""
    from lambda_handler import _upload_db_to_s3

    mock_s3 = MagicMock()
    db_path = str(tmp_path / "portfolio.db")
    db_path_obj = tmp_path / "portfolio.db"
    db_path_obj.write_text("fake db content")

    with (
        patch("lambda_handler.boto3.client", return_value=mock_s3),
        patch("lambda_handler._DB_LOCAL_PATH", db_path),
    ):
        _upload_db_to_s3()

    mock_s3.upload_file.assert_called_once()
    args = mock_s3.upload_file.call_args[0]
    assert args[0] == db_path


def test_handler_uploads_after_write(monkeypatch):
    """Handler uploads DB to S3 after POST/PUT/PATCH/DELETE requests."""
    import lambda_handler

    mock_mangum = MagicMock(return_value={"statusCode": 200})
    monkeypatch.setattr(lambda_handler, "_mangum_handler", mock_mangum)

    upload_calls = []
    monkeypatch.setattr(lambda_handler, "_upload_db_to_s3", lambda: upload_calls.append(1))

    for method in ["POST", "PUT", "PATCH", "DELETE"]:
        upload_calls.clear()
        event = {"requestContext": {"http": {"method": method}}}
        lambda_handler.handler(event, {})
        assert len(upload_calls) == 1, f"Expected upload after {method}"


def test_handler_skips_upload_after_get(monkeypatch):
    """Handler does NOT upload DB to S3 after GET/HEAD requests."""
    import lambda_handler

    mock_mangum = MagicMock(return_value={"statusCode": 200})
    monkeypatch.setattr(lambda_handler, "_mangum_handler", mock_mangum)

    upload_calls = []
    monkeypatch.setattr(lambda_handler, "_upload_db_to_s3", lambda: upload_calls.append(1))

    for method in ["GET", "HEAD"]:
        upload_calls.clear()
        event = {"requestContext": {"http": {"method": method}}}
        lambda_handler.handler(event, {})
        assert len(upload_calls) == 0, f"Should not upload after {method}"


def test_handler_supports_rest_api_payload_v1(monkeypatch):
    """Handler extracts HTTP method from REST API (payload v1) event format."""
    import lambda_handler

    mock_mangum = MagicMock(return_value={"statusCode": 200})
    monkeypatch.setattr(lambda_handler, "_mangum_handler", mock_mangum)

    upload_calls = []
    monkeypatch.setattr(lambda_handler, "_upload_db_to_s3", lambda: upload_calls.append(1))

    # REST API format uses top-level "httpMethod" key
    event = {"httpMethod": "POST"}
    lambda_handler.handler(event, {})
    assert len(upload_calls) == 1
