from unittest.mock import MagicMock, patch

from app.services import playground_service
from app.schemas.playground import PlaygroundMessage


@patch("app.services.playground_service.get_ollama_client")
def test_generate_playground_response_basic(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.return_value = {"message": {"content": "Hi there!"}}
    mock_get_client.return_value = mock_client

    result = playground_service.generate_playground_response(
        messages=[PlaygroundMessage(role="user", content="Hello")],
        model="llama3.2", temperature=0.7, preamble=None,
    )

    assert result.answer == "Hi there!"
    assert result.model == "llama3.2"
    call_kwargs = mock_client.chat.call_args.kwargs
    assert call_kwargs["messages"] == [{"role": "user", "content": "Hello"}]


@patch("app.services.playground_service.get_ollama_client")
def test_generate_playground_response_with_preamble(mock_get_client):
    mock_client = MagicMock()
    mock_client.chat.return_value = {"message": {"content": "answer"}}
    mock_get_client.return_value = mock_client

    playground_service.generate_playground_response(
        messages=[PlaygroundMessage(role="user", content="Hello")],
        model="llama3.2", temperature=0.5, preamble="You are a pirate.",
    )

    sent_messages = mock_client.chat.call_args.kwargs["messages"]
    assert sent_messages[0] == {"role": "system", "content": "You are a pirate."}
    assert sent_messages[1] == {"role": "user", "content": "Hello"}


@patch("app.api.playground.playground_service.generate_playground_response")
def test_playground_chat_endpoint(mock_generate, authenticated_client):
    from app.schemas.playground import PlaygroundChatResponse

    mock_generate.return_value = PlaygroundChatResponse(answer="Hi!", model="llama3.2")
    response = authenticated_client.post(
        "/playground/chat",
        json={"messages": [{"role": "user", "content": "Hello"}], "model": "llama3.2", "temperature": 0.7},
    )
    assert response.status_code == 200
    assert response.json()["answer"] == "Hi!"


def test_playground_chat_requires_auth(client):
    response = client.post(
        "/playground/chat",
        json={"messages": [{"role": "user", "content": "Hello"}], "model": "llama3.2"},
    )
    assert response.status_code == 401