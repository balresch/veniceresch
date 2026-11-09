"""Tests for the decisions (beta) resource."""

from __future__ import annotations

import json

_RESPONSE = {
    "model": "jev-latest",
    "answers": {
        "is_spam": {"type": "noul", "noul": 0.93},
        "tone": {
            "type": "choice",
            "choice": "angry",
            "probabilities": {"angry": 0.8, "calm": 0.2},
            "confidence": 0.7,
        },
    },
    "usage": {"input_tokens": 120, "output_tokens": 4},
}


async def test_create_posts_state_and_questions(mock_api, async_client):
    route = mock_api.post("/decisions").respond(200, json=_RESPONSE)
    questions = {
        "is_spam": {"type": "noul", "instructions": "Is this message spam?"},
        "tone": {
            "type": "choice",
            "instructions": "What is the tone?",
            "criteria": {"angry": None, "calm": "No raised voice"},
        },
    }
    result = await async_client.decisions.create(
        model="jev-latest",
        state=[{"role": "user", "content": "BUY NOW!!!"}],
        questions=questions,
    )
    body = json.loads(route.calls.last.request.content)
    assert body == {
        "model": "jev-latest",
        "state": [{"role": "user", "content": "BUY NOW!!!"}],
        "questions": questions,
    }
    assert result.model == "jev-latest"
    assert result.answers["is_spam"]["noul"] == 0.93
    assert result.answers["tone"]["choice"] == "angry"
    assert result.usage == {"input_tokens": 120, "output_tokens": 4}


def test_create_sync_with_images_and_extra(mock_api, sync_client):
    route = mock_api.post("/decisions").respond(200, json=_RESPONSE)
    sync_client.decisions.create(
        model="clef",
        state="A photo of a receipt",
        questions={
            "score": {"type": "score", "instructions": "Legibility", "criteria": ["a", "b"]}
        },
        images=[
            "data:image/png;base64,AAAA",
            {"content_type": "image/jpeg", "base64": "BBBB"},
        ],
        future_flag=True,
    )
    body = json.loads(route.calls.last.request.content)
    assert body["images"] == [
        "data:image/png;base64,AAAA",
        {"content_type": "image/jpeg", "base64": "BBBB"},
    ]
    assert body["future_flag"] is True
    assert "images" in body and body["model"] == "clef"


def test_create_omits_images_when_none(mock_api, sync_client):
    route = mock_api.post("/decisions").respond(200, json={"model": "m", "answers": {}})
    result = sync_client.decisions.create(model="m", state="s", questions={})
    assert "images" not in json.loads(route.calls.last.request.content)
    assert result.answers == {}
