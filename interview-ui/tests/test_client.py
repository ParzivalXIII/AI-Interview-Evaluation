"""Unit tests for InterviewAPIClient.

All HTTP calls are mocked with respx so no live backend is needed.
"""
from __future__ import annotations

import httpx
import pytest
import respx
from client import APIError, InterviewAPIClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def api_client() -> InterviewAPIClient:
    """Fresh client instance for each test (avoids shared _http state)."""
    return InterviewAPIClient()


# ---------------------------------------------------------------------------
# create_session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_create_session_success(api_client: InterviewAPIClient) -> None:
    respx.post("http://localhost:8000/sessions").mock(
        return_value=httpx.Response(
            201,
            json={
                "sessionId": 42,
                "status": "ready",
                "questions": [
                    {
                        "questionId": 1,
                        "sequenceNumber": 1,
                        "text": "Explain async/await",
                        "type": "coding",
                    }
                ],
            },
        )
    )

    result = await api_client.create_session("Backend Engineer", "mid", 1)

    assert result["session_id"] == 42
    assert result["status"] == "ready"
    assert len(result["questions"]) == 1
    assert result["questions"][0]["question_id"] == 1
    assert result["questions"][0]["text"] == "Explain async/await"
    assert result["questions"][0]["type"] == "coding"


@pytest.mark.asyncio
@respx.mock
async def test_create_session_422(api_client: InterviewAPIClient) -> None:
    respx.post("http://localhost:8000/sessions").mock(
        return_value=httpx.Response(422, json={"detail": "Validation error"})
    )

    with pytest.raises(APIError) as exc_info:
        await api_client.create_session("", "mid", 5)

    assert exc_info.value.status_code == 422
    assert "Validation error" in exc_info.value.message


@pytest.mark.asyncio
@respx.mock
async def test_create_session_500(api_client: InterviewAPIClient) -> None:
    respx.post("http://localhost:8000/sessions").mock(
        return_value=httpx.Response(500, json={"detail": "Internal server error"})
    )

    with pytest.raises(APIError) as exc_info:
        await api_client.create_session("SRE", "senior", 3)

    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
@respx.mock
async def test_create_session_network_error(api_client: InterviewAPIClient) -> None:
    respx.post("http://localhost:8000/sessions").mock(
        side_effect=httpx.ConnectError("Connection refused")
    )

    with pytest.raises(APIError) as exc_info:
        await api_client.create_session("SRE", "mid", 5)

    assert exc_info.value.status_code is None
    assert "Connection error" in exc_info.value.message


# ---------------------------------------------------------------------------
# submit_answer
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_submit_answer_success(api_client: InterviewAPIClient) -> None:
    respx.post("http://localhost:8000/sessions/1/answers").mock(
        return_value=httpx.Response(
            202,
            json={
                "answerId": 7,
                "sessionId": 1,
                "questionId": 1,
                "status": "pending_evaluation",
            },
        )
    )

    result = await api_client.submit_answer(1, 1, "My answer text")

    assert result["answer_id"] == 7
    assert result["session_id"] == 1
    assert result["status"] == "pending_evaluation"


@pytest.mark.asyncio
@respx.mock
async def test_submit_answer_404(api_client: InterviewAPIClient) -> None:
    respx.post("http://localhost:8000/sessions/99/answers").mock(
        return_value=httpx.Response(404, json={"detail": "Session not found"})
    )

    with pytest.raises(APIError) as exc_info:
        await api_client.submit_answer(99, 1, "answer")

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
@respx.mock
async def test_submit_answer_422(api_client: InterviewAPIClient) -> None:
    respx.post("http://localhost:8000/sessions/1/answers").mock(
        return_value=httpx.Response(422, json={"detail": "answerText required"})
    )

    with pytest.raises(APIError) as exc_info:
        await api_client.submit_answer(1, 1, "")

    assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# get_answer_result -- all status values
# ---------------------------------------------------------------------------

_BASE_ANSWER = {
    "answerId": 7,
    "sessionId": 1,
    "questionId": 1,
    "answerText": "My answer",
    "failureReason": None,
    "evaluation": None,
}


@pytest.mark.asyncio
@respx.mock
async def test_get_answer_result_pending(api_client: InterviewAPIClient) -> None:
    respx.get("http://localhost:8000/sessions/1/answers/7").mock(
        return_value=httpx.Response(200, json={**_BASE_ANSWER, "status": "pending_evaluation"})
    )

    result = await api_client.get_answer_result(1, 7)

    assert result["status"] == "pending_evaluation"
    assert result["evaluation"] is None


@pytest.mark.asyncio
@respx.mock
async def test_get_answer_result_in_progress(api_client: InterviewAPIClient) -> None:
    respx.get("http://localhost:8000/sessions/1/answers/7").mock(
        return_value=httpx.Response(200, json={**_BASE_ANSWER, "status": "in_progress"})
    )

    result = await api_client.get_answer_result(1, 7)

    assert result["status"] == "in_progress"


@pytest.mark.asyncio
@respx.mock
async def test_get_answer_result_completed(api_client: InterviewAPIClient) -> None:
    payload = {
        **_BASE_ANSWER,
        "status": "completed",
        "evaluation": {
            "evaluationStatus": "completed",
            "score": 7.5,
            "feedback": "Good answer overall.",
            "strengths": ["Clear explanation"],
            "improvements": ["Add more examples"],
            "schemaVersion": "v1",
            "rubricVersion": "v1",
            "promptVersion": "v1",
            "modelName": "gpt-4o-mini",
        },
    }
    respx.get("http://localhost:8000/sessions/1/answers/7").mock(
        return_value=httpx.Response(200, json=payload)
    )

    result = await api_client.get_answer_result(1, 7)

    assert result["status"] == "completed"
    ev = result["evaluation"]
    assert ev is not None
    assert ev["score"] == 7.5
    assert ev["feedback"] == "Good answer overall."
    assert ev["strengths"] == ["Clear explanation"]
    assert ev["model_name"] == "gpt-4o-mini"


@pytest.mark.asyncio
@respx.mock
async def test_get_answer_result_failed(api_client: InterviewAPIClient) -> None:
    payload = {
        **_BASE_ANSWER,
        "status": "failed",
        "failureReason": "LLM timeout",
    }
    respx.get("http://localhost:8000/sessions/1/answers/7").mock(
        return_value=httpx.Response(200, json=payload)
    )

    result = await api_client.get_answer_result(1, 7)

    assert result["status"] == "failed"
    assert result["failure_reason"] == "LLM timeout"


# ---------------------------------------------------------------------------
# get_session_summary
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_get_session_summary_success(api_client: InterviewAPIClient) -> None:
    respx.get("http://localhost:8000/sessions/1/summary").mock(
        return_value=httpx.Response(
            200,
            json={
                "sessionId": 1,
                "role": "Backend Engineer",
                "difficulty": "mid",
                "status": "completed",
                "questions": [],
            },
        )
    )

    result = await api_client.get_session_summary(1)

    assert result["session_id"] == 1
    assert result["role"] == "Backend Engineer"
    assert result["status"] == "completed"


@pytest.mark.asyncio
@respx.mock
async def test_get_session_summary_404(api_client: InterviewAPIClient) -> None:
    respx.get("http://localhost:8000/sessions/999/summary").mock(
        return_value=httpx.Response(404, json={"detail": "Not found"})
    )

    with pytest.raises(APIError) as exc_info:
        await api_client.get_session_summary(999)

    assert exc_info.value.status_code == 404
