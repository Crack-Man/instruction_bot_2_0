from aiogram.dispatcher.filters.state import StatesGroup, State


class Admin(StatesGroup):
    phone = State()

class FullName(StatesGroup):
    fullname = State()

class NewTest(StatesGroup):
    file = State()
    description = State()

    question1 = State()
    answer11 = State()
    answer12 = State()
    answer13 = State()
    correct1 = State()

    question2 = State()
    answer21 = State()
    answer22 = State()
    answer23 = State()
    correct2 = State()

    question3 = State()
    answer31 = State()
    answer32 = State()
    answer33 = State()
    correct3 = State()

    question4 = State()
    answer41 = State()
    answer42 = State()
    answer43 = State()
    correct4 = State()

class Database(StatesGroup):
    file = State()

class Files(StatesGroup):
    id = State()

class Test(StatesGroup):
    id = State()
    question1 = State()
    question2 = State()
    question3 = State()
    question4 = State()