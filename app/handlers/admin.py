from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from app.config import settings
from app.database.models import TicketStatus
from app.database.session import AsyncSessionLocal
from app.services.tickets import (
    get_ticket_by_id,
    get_ticket_history,
    update_ticket_status,
)


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


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_id_list


@router.callback_query(F.data.startswith("ticket:"))
async def ticket_action_handler(
    callback: CallbackQuery,
    bot: Bot,
) -> None:
    if not is_admin(callback.from_user.id):
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

    try:
        ticket_id = int(ticket_id_text)
    except ValueError:
        await callback.answer(
            "Некорректный номер заявки.",
            show_alert=True,
        )
        return

    if action == "history":
        await show_ticket_history(
            callback=callback,
            ticket_id=ticket_id,
        )
        return

    if action not in ACTION_STATUS:
        await callback.answer(
            "Неизвестное действие.",
            show_alert=True,
        )
        return

    target_status = ACTION_STATUS[action]

    async with AsyncSessionLocal() as session:
        ticket = await get_ticket_by_id(
            session=session,
            ticket_id=ticket_id,
        )

        if ticket is None:
            await callback.answer(
                "Заявка не найдена.",
                show_alert=True,
            )
            return

        if ticket.status == target_status.value:
            current_name = STATUS_NAMES.get(
                ticket.status,
                ticket.status,
            )

            await callback.answer(
                f"Заявка уже имеет статус «{current_name}».",
                show_alert=True,
            )
            return

        if ticket.status in {
            TicketStatus.COMPLETED.value,
            TicketStatus.REJECTED.value,
            TicketStatus.CLOSED.value,
        }:
            await callback.answer(
                "Эта заявка уже завершена и не может быть изменена.",
                show_alert=True,
            )
            return

        ticket = await update_ticket_status(
            session=session,
            ticket_id=ticket_id,
            status=target_status,
            actor_telegram_id=callback.from_user.id,
        )

    if ticket is None:
        await callback.answer(
            "Не удалось изменить заявку.",
            show_alert=True,
        )
        return

    status_name = STATUS_NAMES.get(
        ticket.status,
        ticket.status,
    )

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


async def show_ticket_history(
    callback: CallbackQuery,
    ticket_id: int,
) -> None:
    async with AsyncSessionLocal() as session:
        ticket = await get_ticket_by_id(
            session=session,
            ticket_id=ticket_id,
        )

        if ticket is None:
            await callback.answer(
                "Заявка не найдена.",
                show_alert=True,
            )
            return

        history = await get_ticket_history(
            session=session,
            ticket_id=ticket_id,
        )

    if not history:
        await callback.answer(
            "История заявки пока пуста.",
            show_alert=True,
        )
        return

    lines = [
        f"<b>История заявки №{ticket.id}</b>\n",
    ]

    for item in history:
        old_status = STATUS_NAMES.get(
            item.old_status,
            item.old_status or "—",
        )
        new_status = STATUS_NAMES.get(
            item.new_status,
            item.new_status or "—",
        )

        lines.append(
            f"<b>{item.created_at:%d.%m.%Y %H:%M}</b>\n"
            f"Действие: {item.action}\n"
            f"Статус: {old_status} → {new_status}\n"
            f"Администратор/пользователь: "
            f"{item.actor_telegram_id}\n"
            f"Комментарий: {item.comment or '—'}\n"
        )

    text = "\n".join(lines)

    await callback.answer()

    if callback.message:
        await callback.message.answer(text)