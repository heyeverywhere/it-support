from aiogram import Bot
from aiogram.filters import Command
from app.services.tickets import create_ticket, get_user_tickets
from app.database.session import AsyncSessionLocal
from app.services.tickets import create_ticket
from app.services.notifications import notify_admins_about_new_ticket
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from app.keyboards.user import (
    CANCEL_BUTTON,
    CREATE_TICKET_BUTTON,
    HELP_BUTTON,
    MY_TICKETS_BUTTON,
    confirmation_keyboard,
    main_menu_keyboard,
    phone_request_keyboard,
    priority_keyboard,
    remove_keyboard,
)
from app.states.ticket import TicketForm


router = Router()


@router.message(Command("new_ticket"))
async def new_ticket_handler(
    message: Message,
    state: FSMContext,
) -> None:
    await state.clear()
    await state.set_state(TicketForm.full_name)

    await message.answer(
        "Создание заявки.\n\n"
        "Введите фамилию, имя и отчество:",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(TicketForm.full_name)
async def process_full_name(
    message: Message,
    state: FSMContext,
) -> None:
    full_name = (message.text or "").strip()

    if len(full_name) < 5:
        await message.answer(
            "ФИО указано слишком коротко. "
            "Введите фамилию, имя и отчество."
        )
        return

    await state.update_data(full_name=full_name)
    await state.set_state(TicketForm.phone)

    await message.answer(
        "Передайте номер телефона кнопкой ниже "
        "или введите его вручную.",
        reply_markup=phone_request_keyboard(),
    )


@router.message(TicketForm.phone, F.contact)
async def process_contact(
    message: Message,
    state: FSMContext,
) -> None:
    if message.contact is None:
        await message.answer("Не удалось получить контакт.")
        return

    if message.from_user is None:
        await message.answer("Не удалось определить пользователя.")
        return

    if message.contact.user_id not in (None, message.from_user.id):
        await message.answer(
            "Передайте, пожалуйста, свой номер телефона "
            "через кнопку Telegram."
        )
        return

    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(TicketForm.room_number)

    await message.answer(
        "Введите номер кабинета:",
        reply_markup=remove_keyboard(),
    )


@router.message(TicketForm.phone, F.text)
async def process_phone_text(
    message: Message,
    state: FSMContext,
) -> None:
    phone = (message.text or "").strip()

    if len(phone) < 5:
        await message.answer(
            "Номер телефона выглядит некорректно. "
            "Введите его ещё раз."
        )
        return

    await state.update_data(phone=phone)
    await state.set_state(TicketForm.room_number)

    await message.answer(
        "Введите номер кабинета:",
        reply_markup=remove_keyboard(),
    )


@router.message(TicketForm.room_number)
async def process_room_number(
    message: Message,
    state: FSMContext,
) -> None:
    room_number = (message.text or "").strip()

    if not room_number:
        await message.answer("Номер кабинета не может быть пустым.")
        return

    await state.update_data(room_number=room_number)
    await state.set_state(TicketForm.description)

    await message.answer(
        "Опишите проблему как можно подробнее:"
    )


@router.message(TicketForm.description)
async def process_description(
    message: Message,
    state: FSMContext,
) -> None:
    description = (message.text or "").strip()

    if len(description) < 5:
        await message.answer(
            "Описание слишком короткое. "
            "Опишите проблему подробнее."
        )
        return

    await state.update_data(description=description)
    await state.set_state(TicketForm.priority)

    await message.answer(
        "Выберите степень срочности:",
        reply_markup=priority_keyboard(),
    )


@router.message(TicketForm.priority)
async def process_priority(
    message: Message,
    state: FSMContext,
) -> None:
    priority = (message.text or "").strip()
    allowed_priorities = {
        "Критическая",
        "Высокая",
        "Средняя",
        "Низкая",
    }

    if priority == "Отмена":
        await state.clear()
        await message.answer(
            "Создание заявки отменено.",
            reply_markup=remove_keyboard(),
        )
        return

    if priority not in allowed_priorities:
        await message.answer(
            "Выберите срочность с помощью кнопок."
        )
        return

    await state.update_data(priority=priority)
    data = await state.get_data()
    await state.set_state(TicketForm.confirmation)

    summary = (
        "Проверьте данные заявки:\n\n"
        f"<b>ФИО:</b> {data['full_name']}\n"
        f"<b>Телефон:</b> {data['phone']}\n"
        f"<b>Кабинет:</b> {data['room_number']}\n"
        f"<b>Описание:</b> {data['description']}\n"
        f"<b>Срочность:</b> {data['priority']}\n\n"
        "Отправить заявку?"
    )

    await message.answer(
        summary,
        reply_markup=confirmation_keyboard(),
    )


@router.message(TicketForm.confirmation, F.text == "Подтвердить")
async def confirm_ticket(
    message: Message,
    state: FSMContext,
    bot: Bot,
) -> None:
    if message.from_user is None:
        await message.answer(
            "Не удалось определить пользователя."
        )
        return

    data = await state.get_data()

    async with AsyncSessionLocal() as session:
        ticket = await create_ticket(
            session=session,
            telegram_user_id=message.from_user.id,
            full_name=data["full_name"],
            phone=data["phone"],
            room_number=data["room_number"],
            description=data["description"],
            priority=data["priority"],
        )

    await notify_admins_about_new_ticket(
        bot=bot,
        ticket=ticket,
    )

    await state.clear()

    await message.answer(
        f"Заявка №{ticket.id} успешно создана.\n\n"
        "Администратор получил информацию и рассмотрит её.",
        reply_markup=main_menu_keyboard(),
    )

@router.message(TicketForm.confirmation, F.text == "Изменить")
async def edit_ticket(
    message: Message,
    state: FSMContext,
) -> None:
    await state.set_state(TicketForm.full_name)

    await message.answer(
        "Введите ФИО заново:",
        reply_markup=main_menu_keyboard(),
    )


@router.message(TicketForm.confirmation, F.text == "Отмена")
async def cancel_ticket(
    message: Message,
    state: FSMContext,
) -> None:
    await state.clear()

    await message.answer(
        "Создание заявки отменено.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(TicketForm.confirmation)
async def invalid_confirmation(
    message: Message,
) -> None:
    await message.answer(
        "Используйте кнопки «Подтвердить», "
        "«Изменить» или «Отмена»."
    )

@router.message(Command("my_tickets"))
async def my_tickets_handler(message: Message) -> None:
    if message.from_user is None:
        await message.answer(
            "Не удалось определить пользователя."
        )
        return

    async with AsyncSessionLocal() as session:
        tickets = await get_user_tickets(
            session=session,
            telegram_user_id=message.from_user.id,
        )

    if not tickets:
        await message.answer(
            "У вас пока нет заявок."
        )
        return

    lines = ["Ваши заявки:\n"]

    for ticket in tickets:
        lines.append(
            f"№{ticket.id} | "
            f"{ticket.status} | "
            f"{ticket.priority}\n"
            f"Кабинет: {ticket.room_number}\n"
            f"{ticket.description}\n"
        )

    await message.answer("\n".join(lines))

@router.message(F.text == CREATE_TICKET_BUTTON)
async def create_ticket_button_handler(
    message: Message,
    state: FSMContext,
) -> None:
    await new_ticket_handler(message, state)


@router.message(F.text == MY_TICKETS_BUTTON)
async def my_tickets_button_handler(message: Message) -> None:
    await my_tickets_handler(message)


@router.message(F.text == HELP_BUTTON)
async def help_button_handler(message: Message) -> None:
    await message.answer(
        "<b>Как создать заявку</b>\n\n"
        "1. Нажмите «Создать заявку».\n"
        "2. Укажите ФИО, телефон и кабинет.\n"
        "3. Опишите проблему.\n"
        "4. Выберите срочность.\n"
        "5. Проверьте данные и подтвердите заявку.\n\n"
        "Если проблема связана с персональными данными пациента, "
        "не отправляйте такие сведения в чат."
    )