from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Ticket, TicketStatus


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