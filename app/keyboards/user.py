from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)


CREATE_TICKET_BUTTON = "Создать заявку"
MY_TICKETS_BUTTON = "Мои заявки"
HELP_BUTTON = "Помощь"
CANCEL_BUTTON = "Отмена"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=CREATE_TICKET_BUTTON),
                KeyboardButton(text=MY_TICKETS_BUTTON),
            ],
            [
                KeyboardButton(text=HELP_BUTTON),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Выберите действие",
    )


def phone_request_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="Передать номер телефона",
                    request_contact=True,
                )
            ],
            [
                KeyboardButton(text=CANCEL_BUTTON),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def priority_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Критическая"),
                KeyboardButton(text="Высокая"),
            ],
            [
                KeyboardButton(text="Средняя"),
                KeyboardButton(text="Низкая"),
            ],
            [
                KeyboardButton(text=CANCEL_BUTTON),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def confirmation_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Подтвердить"),
                KeyboardButton(text="Изменить"),
            ],
            [
                KeyboardButton(text=CANCEL_BUTTON),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()