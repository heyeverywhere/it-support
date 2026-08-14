from aiogram.fsm.state import State, StatesGroup


class TicketForm(StatesGroup):
    full_name = State()
    phone = State()
    room_number = State()
    description = State()
    priority = State()
    confirmation = State()