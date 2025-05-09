from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_statistics_menu_keyboard() -> InlineKeyboardMarkup:
    """Get statistics menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="📊 Overall Statistics",
                callback_data="stats_overall"
            )
        ],
        [
            InlineKeyboardButton(
                text="📈 Progress Over Time",
                callback_data="stats_progress"
            )
        ],
        [
            InlineKeyboardButton(
                text="👥 Class Statistics",
                callback_data="stats_class"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_subject_selection_keyboard(subjects: list) -> InlineKeyboardMarkup:
    """Get subject selection keyboard"""
    keyboard = []
    for subject in subjects:
        keyboard.append([
            InlineKeyboardButton(
                text=subject["name"],
                callback_data=f"subject_{subject['id']}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_time_period_keyboard() -> InlineKeyboardMarkup:
    """Get time period selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="Last 7 days",
                callback_data="period_7"
            )
        ],
        [
            InlineKeyboardButton(
                text="Last 30 days",
                callback_data="period_30"
            )
        ],
        [
            InlineKeyboardButton(
                text="Last 90 days",
                callback_data="period_90"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 