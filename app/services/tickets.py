from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    Ticket,
    TicketHistory,
    TicketStatus,
)


async def create_ticket(
    session: AsyncSession,
    telegram_user_id: int,
    full_name: str,
    phone: str,
    room_number: str,
    description: str,
    priority: str,
) -> Ticket:
    ticket = Ticket(
        telegram_user_id=telegram_user_id,
        full_name=full_name,
        phone=phone,
        room_number=room_number,
        description=description,
        priority=priority,
        status=TicketStatus.NEW.value,
    )

    session.add(ticket)
    await session.flush()

    history = TicketHistory(
        ticket_id=ticket.id,
        actor_telegram_id=telegram_user_id,
        action="created",
        old_status=None,
        new_status=TicketStatus.NEW.value,
        comment="Заявка создана пользователем.",
    )

    session.add(history)

    await session.commit()
    await session.refresh(ticket)

    return ticket


async def get_user_tickets(
    session: AsyncSession,
    telegram_user_id: int,
) -> list[Ticket]:
    result = await session.execute(
        select(Ticket)
        .where(Ticket.telegram_user_id == telegram_user_id)
        .order_by(Ticket.created_at.desc())
    )

    return list(result.scalars().all())


async def get_ticket_by_id(
    session: AsyncSession,
    ticket_id: int,
) -> Ticket | None:
    result = await session.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )

    return result.scalar_one_or_none()


async def update_ticket_status(
    session: AsyncSession,
    ticket_id: int,
    status: TicketStatus,
    actor_telegram_id: int,
    comment: str | None = None,
) -> Ticket | None:
    ticket = await get_ticket_by_id(
        session=session,
        ticket_id=ticket_id,
    )

    if ticket is None:
        return None

    old_status = ticket.status

    if old_status == status.value:
        return ticket

    ticket.status = status.value

    if status == TicketStatus.COMPLETED:
        ticket.completed_at = datetime.utcnow()
    else:
        ticket.completed_at = None

    history = TicketHistory(
        ticket_id=ticket.id,
        actor_telegram_id=actor_telegram_id,
        action="status_changed",
        old_status=old_status,
        new_status=status.value,
        comment=comment,
    )

    session.add(history)

    await session.commit()
    await session.refresh(ticket)

    return ticket


async def get_ticket_history(
    session: AsyncSession,
    ticket_id: int,
) -> list[TicketHistory]:
    result = await session.execute(
        select(TicketHistory)
        .where(TicketHistory.ticket_id == ticket_id)
        .order_by(TicketHistory.created_at.asc())
    )

    return list(result.scalars().all())