from aiogram import Bot

from app.config import settings
from app.database.models import Ticket
from app.keyboards.admin import new_ticket_keyboard


async def notify_admins_about_new_ticket(
    bot: Bot,
    ticket: Ticket,
) -> None:
    if not settings.admin_id_list:
        return

    text = (
        "<b>Новая заявка технической поддержки</b>\n\n"
        f"<b>Номер:</b> №{ticket.id}\n"
        f"<b>ФИО:</b> {ticket.full_name}\n"
        f"<b>Телефон:</b> {ticket.phone}\n"
        f"<b>Кабинет:</b> {ticket.room_number}\n"
        f"<b>Срочность:</b> {ticket.priority}\n"
        f"<b>Описание:</b> {ticket.description}\n"
    )

    for admin_id in settings.admin_id_list:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=text,
                reply_markup=new_ticket_keyboard(ticket.id),
            )
        except Exception:
            continue