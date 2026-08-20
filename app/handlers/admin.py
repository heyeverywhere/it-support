from aiogram import F, Router, Bot
from aiogram.types import CallbackQuery

from app.config import settings
from app.database.models import TicketStatus
from app.database.session import AsyncSessionLocal
from app.services.tickets import update_ticket_status


router = Router()


STATUS_NAMES = {
    TicketStatus.NEW.value: "Новая",
    TicketStatus.IN_PROGRESS.value: "Принята в работу",
    TicketStatus.COMPLETED.value: "Выполнена",
    TicketStatus.REJECTED.value: "Отклонена",
    TicketStatus.CLOSED.value: "Закрыта",
}


ACTION_STATUS = {
    "accept": TicketStatus.IN_PROGRESS,
    "complete": TicketStatus.COMPLETED,
    "reject": TicketStatus.REJECTED,
}


@router.callback_query(F.data.startswith("ticket:"))
async def ticket_action_handler(
    callback: CallbackQuery,
    bot: Bot,
) -> None:
    if callback.from_user.id not in settings.admin_id_list:
        await callback.answer(
            "У вас нет прав администратора.",
            show_alert=True,
        )
        return

    parts = (callback.data or "").split(":")

    if len(parts) != 3:
        await callback.answer(
            "Некорректная команда.",
            show_alert=True,
        )
        return

    _, action, ticket_id_text = parts

    if action not in ACTION_STATUS:
        await callback.answer(
            "Неизвестное действие.",
            show_alert=True,
        )
        return

    try:
        ticket_id = int(ticket_id_text)
    except ValueError:
        await callback.answer(
            "Некорректный номер заявки.",
            show_alert=True,
        )
        return

    async with AsyncSessionLocal() as session:
        ticket = await update_ticket_status(
            session=session,
            ticket_id=ticket_id,
            status=ACTION_STATUS[action],
        )

    if ticket is None:
        await callback.answer(
            "Заявка не найдена.",
            show_alert=True,
        )
        return

    status_name = STATUS_NAMES[ticket.status]

    await callback.answer(
        f"Заявка №{ticket.id}: {status_name}"
    )

    if callback.message:
        await callback.message.edit_reply_markup(
            reply_markup=None,
        )

        await callback.message.answer(
            f"Статус заявки №{ticket.id} изменён: "
            f"<b>{status_name}</b>."
        )

    try:
        await bot.send_message(
            chat_id=ticket.telegram_user_id,
            text=(
                f"Статус вашей заявки №{ticket.id} изменён.\n\n"
                f"<b>Новый статус:</b> {status_name}"
            ),
        )
    except Exception:
        pass