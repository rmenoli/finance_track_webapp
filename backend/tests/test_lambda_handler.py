"""Tests for lambda_handler."""

from unittest.mock import MagicMock


def test_handler_delegates_to_mangum(monkeypatch):
    """handler() delegates the event and context to the Mangum adapter."""
    import lambda_handler

    mock_response = {"statusCode": 200, "body": "ok"}
    mock_mangum = MagicMock(return_value=mock_response)
    monkeypatch.setattr(lambda_handler, "_mangum_handler", mock_mangum)

    event = {"requestContext": {"http": {"method": "GET"}}, "rawPath": "/api/v1/health"}
    context = object()
    result = lambda_handler.handler(event, context)

    mock_mangum.assert_called_once_with(event, context)
    assert result == mock_response


def test_handler_passes_write_events_without_side_effects(monkeypatch):
    """handler() passes write-method events through Mangum with no S3 side effects."""
    import lambda_handler

    mock_mangum = MagicMock(return_value={"statusCode": 201})
    monkeypatch.setattr(lambda_handler, "_mangum_handler", mock_mangum)

    for method in ["POST", "PUT", "PATCH", "DELETE"]:
        event = {"requestContext": {"http": {"method": method}}}
        result = lambda_handler.handler(event, {})
        assert result == {"statusCode": 201}
        mock_mangum.assert_called_with(event, {})
