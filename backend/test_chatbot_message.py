"""
Tests for POST /api/chatbot/message.

Runs the real endpoint and the real google-generativeai SDK; only the final
network call (GenerativeServiceClient.generate_content) is intercepted, so the
assertions check the exact request Gemini would receive.

Run: ./venv/bin/python -m pytest test_chatbot_message.py -v
"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from google.ai.generativelanguage_v1beta.services.generative_service.client import GenerativeServiceClient
from google.ai.generativelanguage_v1beta.types import (
    Candidate, Content, GenerateContentResponse, Part,
)

import server

GREETING = ('Hello! I am NutriBot, your personal nutrition assistant. I can provide diet and nutrition '
            'advice based on your profile. Please note: I am not a substitute for professional medical '
            'advice. Always consult a healthcare provider for medical decisions.')
ERROR_BUBBLE = 'Sorry, there was an error connecting to the nutrition assistant.'

# Shape of the UserProfile the app sends (getUserProfileSafe result), including empty fields
APP_PROFILE = {
    "firstName": "Asha", "lastName": "Mehra", "age": 34, "gender": "female",
    "email": "asha@example.com", "currentWeight": 72, "goalWeight": 62, "height": 160,
    "dietaryPreference": "vegetarian", "favouriteCuisine": "North Indian",
    "allergies": "peanuts", "medicalConditions": "PCOS", "targetCalories": 1600,
    "targetProtein": 80, "targetFat": 50, "activityLevel": "moderate",
    "caloriesBurnedGoal": 300, "stepGoal": None, "dietPdfUrl": None,
}

client = TestClient(server.app)


@pytest.fixture
def gemini():
    """Intercept the outgoing Gemini request; yields a dict to inspect / configure."""
    state = {"requests": [], "reply": "Here is some advice.", "empty": None}

    def fake_generate_content(self, request=None, **kwargs):
        state["requests"].append(request)
        if state["empty"]:
            return GenerateContentResponse(candidates=[Candidate(finish_reason=state["empty"])])
        return GenerateContentResponse(candidates=[Candidate(
            content=Content(role="model", parts=[Part(text=state["reply"])]),
            finish_reason=Candidate.FinishReason.STOP,
        )])

    with patch.object(GenerativeServiceClient, "generate_content", fake_generate_content):
        yield state


def send(history, message, profile=APP_PROFILE, user_id="test-user-1"):
    return client.post("/api/chatbot/message", json={
        "userId": user_id, "chat_history": history,
        "user_profile": profile, "user_message": message,
    })


def turns(request):
    return [(c.role, "".join(p.text for p in c.parts)) for c in request.contents]


def all_text(request):
    return "\n".join(text for _, text in turns(request))


# --- Bug fix: latest message is sent exactly once ---------------------------

def test_first_message_sent_once_as_final_turn(gemini):
    r = send([{"sender": "bot", "text": GREETING}], "what should I eat for breakfast?")
    assert r.status_code == 200
    assert r.json() == {"bot_message": "Here is some advice."}
    t = turns(gemini["requests"][0])
    assert [role for role, _ in t] == ["user", "model", "user"]
    assert t[1][1] == GREETING
    assert t[-1] == ("user", "what should I eat for breakfast?")
    assert all_text(gemini["requests"][0]).count("what should I eat for breakfast?") == 1


@pytest.mark.parametrize("short", ["2", "7", "yes", "ok", "no"])
def test_short_reply_not_doubled(gemini, short):
    history = [
        {"sender": "bot", "text": GREETING},
        {"sender": "user", "text": "I want to lose weight"},
        {"sender": "bot", "text": "Would you like 1) meal ideas or 2) exercise tips?"},
    ]
    assert send(history, short).status_code == 200
    t = turns(gemini["requests"][0])
    assert t[-1] == ("user", short)          # exactly "2", never "22"
    assert t[-2][0] == "model"               # roles alternate, nothing merged into it
    assert [role for role, _ in t] == ["user", "model", "user", "model", "user"]


def test_multi_turn_conversation_like_app(gemini):
    """Replays ChatbotScreen: history = messages before the new one, bot replies appended."""
    history = [{"sender": "bot", "text": GREETING}]
    for i, q in enumerate(["breakfast ideas?", "and lunch?", "thanks"]):
        gemini["reply"] = f"answer {i}"
        r = send(history, q)
        assert r.status_code == 200
        t = turns(gemini["requests"][-1])
        assert t[-1] == ("user", q)
        assert all_text(gemini["requests"][-1]).count(q) == 1
        assert [role for role, _ in t] == ["user"] + ["model", "user"] * (i + 1)
        history += [{"sender": "user", "text": q}, {"sender": "bot", "text": r.json()["bot_message"]}]
    # earlier bot answers are carried forward as model turns
    assert ("model", "answer 0") in turns(gemini["requests"][-1])


def test_current_message_already_in_history_not_duplicated(gemini):
    history = [{"sender": "bot", "text": GREETING}, {"sender": "user", "text": "2"}]
    assert send(history, "2").status_code == 200
    t = turns(gemini["requests"][0])
    assert t[-1] == ("user", "2")
    assert [role for role, _ in t] == ["user", "model", "user"]


def test_client_error_and_typing_bubbles_are_not_sent_as_model_turns(gemini):
    history = [
        {"sender": "bot", "text": GREETING},
        {"sender": "user", "text": "is paneer ok?"},
        {"sender": "bot", "text": ERROR_BUBBLE},
        {"sender": "bot", "text": "Typing..."},
    ]
    assert send(history, "is paneer ok?").status_code == 200
    text = all_text(gemini["requests"][0])
    assert ERROR_BUBBLE not in text and "Typing..." not in text
    # the retried question is sent once, not merged with the failed attempt
    assert text.count("is paneer ok?") == 1


# --- Profile is still read ------------------------------------------------

def test_profile_is_in_system_turn(gemini):
    assert send([{"sender": "bot", "text": GREETING}], "hi").status_code == 200
    role, system = turns(gemini["requests"][0])[0]
    assert role == "user"
    assert system.startswith("You are NutriBot")
    for line in ["firstName: Asha", "age: 34", "gender: female", "currentWeight: 72",
                 "goalWeight: 62", "height: 160", "dietaryPreference: vegetarian",
                 "favouriteCuisine: North Indian", "allergies: peanuts",
                 "medicalConditions: PCOS", "targetCalories: 1600", "activityLevel: moderate"]:
        assert line in system, line
    assert "stepGoal" not in system and "dietPdfUrl" not in system  # empty fields skipped
    assert "Never change or update user information" in system


def test_profile_sent_on_every_turn(gemini):
    history = [{"sender": "bot", "text": GREETING}]
    for q in ["hi", "yes", "2"]:
        send(history, q)
        history += [{"sender": "user", "text": q}, {"sender": "bot", "text": "reply"}]
    for req in gemini["requests"]:
        assert "allergies: peanuts" in turns(req)[0][1]


def test_app_fallback_profile_still_used(gemini):
    """ChatbotScreen sends this when the real profile has not loaded yet."""
    fallback = {"firstName": "User", "lastName": "", "age": 25, "gender": "other", "email": "x@example.com"}
    assert send([{"sender": "bot", "text": GREETING}], "hi", profile=fallback).status_code == 200
    system = turns(gemini["requests"][0])[0][1]
    assert "firstName: User" in system and "age: 25" in system


def test_diet_pdf_context_included(gemini):
    profile = {**APP_PROFILE, "dietPdfUrl": "diet_week1.pdf"}
    diet_text = "Breakfast: Moong dal chilla\nLunch: 2 roti + palak paneer\nDinner: Vegetable soup"
    with patch.object(server.pdf_rag_service, "get_diet_pdf_text", return_value=diet_text) as get_text:
        assert send([{"sender": "bot", "text": GREETING}], "what is my lunch?", profile=profile,
                    user_id="user-with-diet").status_code == 200
    assert get_text.call_args[0][:2] == ("user-with-diet", "diet_week1.pdf")
    system = turns(gemini["requests"][0])[0][1]
    assert "CURRENT DIET PLAN INFORMATION" in system
    assert "Lunch: 2 roti + palak paneer" in system
    assert "allergies: peanuts" in system  # profile kept alongside the diet
    assert turns(gemini["requests"][0])[-1] == ("user", "what is my lunch?")


def test_diet_pdf_failure_still_answers_with_profile(gemini):
    profile = {**APP_PROFILE, "dietPdfUrl": "diet_week1.pdf"}
    with patch.object(server.pdf_rag_service, "get_diet_pdf_text", side_effect=RuntimeError("storage down")):
        r = send([{"sender": "bot", "text": GREETING}], "what is my lunch?", profile=profile)
    assert r.status_code == 200
    system = turns(gemini["requests"][0])[0][1]
    assert "allergies: peanuts" in system and "CURRENT DIET PLAN INFORMATION" not in system


# --- Other behaviour ------------------------------------------------------

def test_empty_history(gemini):
    assert send([], "hello").status_code == 200
    assert turns(gemini["requests"][0])[-1] == ("user", "hello")
    assert [role for role, _ in turns(gemini["requests"][0])] == ["user", "user"]


def test_gemini_returns_no_text_gives_clear_500(gemini):
    # MAX_TOKENS with no text passes the SDK's own checks; .text then raises ValueError
    gemini["empty"] = Candidate.FinishReason.MAX_TOKENS
    r = send([{"sender": "bot", "text": GREETING}], "hi")
    assert r.status_code == 500
    assert "Gemini returned no text" in r.json()["detail"]
    assert "finish_reason=2" in r.json()["detail"]  # 2 = MAX_TOKENS


def test_gemini_safety_block_gives_500(gemini):
    gemini["empty"] = Candidate.FinishReason.SAFETY
    r = send([{"sender": "bot", "text": GREETING}], "hi")
    assert r.status_code == 500
