import pytest
from unittest.mock import patch, AsyncMock
from aiogram import Bot, Dispatcher
from aiogram.types import CallbackQuery, User as TelegramUser
from uuid import uuid4

from tg_bot.routers.user.welcome import show_statistics


@pytest.fixture
def bot():
    return Bot(token="dummy_token")


@pytest.fixture
def dp():
    return Dispatcher()


@pytest.fixture
def mock_callback():

    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = AsyncMock(spec=TelegramUser)
    callback.from_user.id = 123456789
    callback.message = AsyncMock()
    return callback


@pytest.mark.asyncio
async def test_show_statistics(bot, dp):
    callback_query = CallbackQuery(
        id="123",
        from_user=TelegramUser(id=123456, is_bot=False, first_name="Test"),
        chat_instance="test_chat",
        message=None,
        data="show_statistics",
    )

    mock_response = {
        "grades": {"distribution": {"5": 10, "4": 5, "3": 2}, "average": 4.5},
        "attendance": {
            "total_days": 100,
            "present_days": 90,
            "absent_days": 8,
            "late_days": 2,
        },
    }

    with patch(
        "tg_bot.routers.user.welcome.make_api_request", new_callable=AsyncMock
    ) as mock_api:
        mock_api.return_value = mock_response

        await show_statistics(callback_query, bot)

        mock_api.assert_called_once_with(
            "GET",
            f"/statistics/student/{callback_query.from_user.id}",
            params={"chat_id": callback_query.from_user.id},
        )

        assert mock_api.called


@pytest.mark.asyncio
async def test_show_statistics_success(mock_callback, bot):

    user_data = {"uuid": str(uuid4()), "role": "student", "name": "Test Student"}

    stats_data = {
        "grades": {"distribution": {"5": 2, "4": 1}, "average": 4.67},
        "attendance": {
            "total_days": 100,
            "present_days": 90,
            "absent_days": 8,
            "late_days": 2,
        },
    }

    with patch("tg_bot.routers.user.welcome.make_api_request") as mock_request:
        mock_request.side_effect = [
            AsyncMock(status_code=200, json=lambda: user_data),
            AsyncMock(status_code=200, json=lambda: stats_data),
        ]

        await show_statistics(mock_callback, bot)

        mock_request.assert_any_call(
            "GET", f"/user?chat_id={mock_callback.from_user.id}"
        )
        mock_request.assert_any_call("GET", f"/statistics/student/{user_data['uuid']}")

        mock_callback.message.answer.assert_called_once()
        message_text = mock_callback.message.answer.call_args[0][0]

        assert "📊 Your Statistics:" in message_text
        assert "📚 Grades:" in message_text
        assert "2 5 grades" in message_text
        assert "1 4 grade" in message_text
        assert "Average Grade: 4.67" in message_text
        assert "📅 Attendance:" in message_text
        assert "90 days present" in message_text
        assert "8 days absent" in message_text
        assert "2 days late" in message_text


@pytest.mark.asyncio
async def test_show_statistics_user_not_found(mock_callback, bot):

    with patch("tg_bot.routers.user.welcome.make_api_request") as mock_request:
        mock_request.return_value = None

        await show_statistics(mock_callback, bot)

        mock_callback.message.answer.assert_called_once_with(
            "❌ Failed to get user data. Please try again later."
        )


@pytest.mark.asyncio
async def test_show_statistics_stats_not_found(mock_callback, bot):

    user_data = {"uuid": str(uuid4()), "role": "student", "name": "Test Student"}

    with patch("tg_bot.routers.user.welcome.make_api_request") as mock_request:
        mock_request.side_effect = [
            AsyncMock(status_code=200, json=lambda: user_data),
            None,
        ]

        await show_statistics(mock_callback, bot)

        mock_callback.message.answer.assert_called_once_with(
            "❌ Failed to get statistics. Please try again later."
        )


@pytest.mark.asyncio
async def test_show_statistics_no_grades(mock_callback, bot):

    user_data = {"uuid": str(uuid4()), "role": "student", "name": "Test Student"}

    stats_data = {
        "grades": {"distribution": {}, "average": None},
        "attendance": {
            "total_days": 100,
            "present_days": 90,
            "absent_days": 8,
            "late_days": 2,
        },
    }

    with patch("tg_bot.routers.user.welcome.make_api_request") as mock_request:
        mock_request.side_effect = [
            AsyncMock(status_code=200, json=lambda: user_data),
            AsyncMock(status_code=200, json=lambda: stats_data),
        ]

        await show_statistics(mock_callback, bot)

        mock_callback.message.answer.assert_called_once()
        message_text = mock_callback.message.answer.call_args[0][0]

        assert "📊 Your Statistics:" in message_text
        assert "📚 Grades:" in message_text
        assert "Average Grade:" not in message_text
        assert "📅 Attendance:" in message_text
        assert "90 days present" in message_text
        assert "8 days absent" in message_text
        assert "2 days late" in message_text


@pytest.mark.asyncio
async def test_show_statistics_no_permission(mock_callback):

    user_data = {"uuid": str(uuid4()), "role": "student", "name": "Test Student"}

    with patch("tg_bot.routers.user.welcome.make_api_request") as mock_request:
        mock_request.side_effect = [
            AsyncMock(status_code=200, json=lambda: user_data),
            AsyncMock(status_code=403),
        ]

        await show_statistics(mock_callback)

        mock_callback.message.answer.assert_called_once_with(
            "❌ You don't have permission to view these statistics."
        )
