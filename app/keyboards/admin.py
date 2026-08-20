from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def new_ticket_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Принять в работу",
                    callback_data=f"ticket:accept:{ticket_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Завершить",
                    callback_data=f"ticket:complete:{ticket_id}",
                ),
                InlineKeyboardButton(
                    text="Отклонить",
                    callback_data=f"ticket:reject:{ticket_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="История",
                    callback_data=f"ticket:history:{ticket_id}",
                ),
            ],
        ]
    )