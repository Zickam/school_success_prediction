from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_grades_menu_keyboard() -> InlineKeyboardMarkup:

    keyboard = [
        [InlineKeyboardButton(text="📚 Recent Grades", callback_data="grades_recent")],
        [
            InlineKeyboardButton(
                text="📝 Grades by Subject", callback_data="grades_subject"
            )
        ],
        [
            InlineKeyboardButton(
                text="📅 Grades by Period", callback_data="grades_period"
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 Grade Statistics", callback_data="grades_stats"
            )
        ],
        [InlineKeyboardButton(text="🔙 Back to Menu", callback_data="menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_subject_selection_keyboard(subjects: list) -> InlineKeyboardMarkup:

    keyboard = []
    for subject in subjects:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=subject["name"], callback_data=f"subject_{subject['id']}"
                )
            ]
        )
    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="grades_back")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_time_period_keyboard() -> InlineKeyboardMarkup:

    keyboard = [
        [InlineKeyboardButton(text="Last 7 days", callback_data="period_7")],
        [InlineKeyboardButton(text="Last 30 days", callback_data="period_30")],
        [InlineKeyboardButton(text="Last 90 days", callback_data="period_90")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="grades_back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
