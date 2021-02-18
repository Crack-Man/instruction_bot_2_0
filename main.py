import os
import urllib
from time import sleep

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from config import Config
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

import logging

from sql_requests import Requests
from states import Admin, FullName, NewTest, Database, Files, Test
import datetime
import time

import xlwt

logging.basicConfig(level=logging.INFO)

# Логгер ошибок
# logger = logging.getLogger("logger")
# logger.setLevel(logging.ERROR)
# fh = logging.FileHandler("logging.log")
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s\n\n%(message)s\n\n\n\n')
# logger.setFormatter(formatter)
# logger.addHandler(fh)

# Класс Config() содержит токен бота, в целях безопасности содержимое класса в GitHub отсутствует
cfg = Config()
TOKEN = cfg.getToken()
bot = Bot(token=TOKEN)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

db = Requests('db.db')

menu = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="/docs - список документов")
            ],
            [
                KeyboardButton(text="/get - получить файл документа")
            ],
            [
                KeyboardButton(text="/test - пройти тест")
            ],
            [
                KeyboardButton(text="/myresults - посмотреть собственные результаты сдачи тестов")
            ]
        ],
        resize_keyboard = True
    )

menu_admin = menu.add(KeyboardButton(text="/adminpanel - открыть панель администратора"))
menu_admin_list =  ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="/back - назад")
            ],
            [
                KeyboardButton(text="/get_users - список пользователей")
            ],
            [
                KeyboardButton(text="/results - результаты сдачи тестов сотрудниками")
            ],
            [
                KeyboardButton(text="/upload - загрузить документ и создать опрос к нему")
            ],
            [
                KeyboardButton(text="/get_db - получить файл базы данных")
            ],
            [
                KeyboardButton(text="/set_db - отправить файл базы данных")
            ],
            [
                KeyboardButton(text="/admin - выдать права администратора пользователю")
            ]
        ],
        resize_keyboard = True
)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    phone = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Отправить номер телефона", request_contact=True)
            ]
        ]
    )
    id_user = message.from_user.id
    if not db.user_exists(id_user):
        db.add_user(id_user, message.from_user.username)
    # await message.answer('/help - список команд')
    if not db.check_phone(id_user)[0]:
        await message.answer("Дайте доступ к номеру телефона. Для этого нажмите кнопку 'Отправить номер телефона'. Если вы не видите кнопку, возможно, вы её скрыли", reply_markup=phone)
        sleep(1)
        directory = "photo_button.png"
        with open(directory, "rb") as f:
            await message.answer_photo(f, "Если кнопка скрыта, нажмите сюда")
    elif not db.check_fullname(id_user)[0]:
        await message.answer("Введите ваше ФИО")
        await FullName.fullname.set()
    else:
        await message.answer('Для выполнения команд нажмите соответствующую кнопку', reply_markup = menu_admin if db.user_is_admin(message.from_user.id) else menu)

@dp.message_handler(commands=['back'])
async def phone(message: types.Message):
    if db.user_is_admin(message.from_user.id):
        await message.answer('Панель администратора', reply_markup = menu_admin if db.user_is_admin(message.from_user.id) else menu)
    else:
        await message.answer('У вас нет прав')

@dp.message_handler(commands=['adminpanel'])
async def phone(message: types.Message):
    if db.user_is_admin(message.from_user.id):
        await message.answer('Панель администратора', reply_markup = menu_admin_list)
    else:
        await message.answer('У вас нет прав')

@dp.message_handler(content_types=['contact'])
async def phone(message: types.Message):
    db.set_phone(message.from_user.id, message.contact["phone_number"])
    await message.answer("Благодарим за предоставление номера телефона", reply_markup=ReplyKeyboardRemove())
    if not db.check_fullname(message.from_user.id)[0]:
        await message.answer("Введите ваше ФИО")
        await FullName.fullname.set()

@dp.message_handler(state=FullName.fullname)
async def set_fullname(message: types.Message, state: FSMContext):
    db.set_fullname(message.from_user.id, message.text)
    await message.answer("Данные обновлены")
    await message.answer('Для выполнения команд нажмите соответствующую кнопку', reply_markup = menu_admin if db.user_is_admin(message.from_user.id) else menu)
    await state.finish()

@dp.message_handler(commands=['help'])
async def help(message: types.Message):
    text = (
        "<b>Список команд:</b>\n"
        "/docs - список документов\n"
        "/get - получить файл документа\n"
        "/test - пройти тест\n"
        "/myresults - посмотреть собственные результаты сдачи тестов\n\n"
        'Введите "." если хотите отменить введённую команду (кроме ситуаций прохождения теста)'
    )

    text_admin = (
        "\n\n<b>Для администраторов:</b>\n"
        "/get_users - получить список пользователей\n"
        "/results - результаты сдачи тестов сотрудниками\n"
        "/upload - загрузить документ и создать опрос к нему\n\n"
        "<b>Только для опытных пользователей:</b>\n"
        "/get_db - получить файл базы данных\n"
        "/set_db - отправить файл базы данных\n"
        "/admin - выдать права администратора пользователю"
    )
    if db.user_is_admin(message.from_user.id):
        text += text_admin
    await message.answer(text, parse_mode='html')

@dp.message_handler(commands=['admin'])
async def set_admin(message: types.Message):
    if db.user_is_admin(message.from_user.id):
        back = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="/back - назад")
                ]
            ],
            resize_keyboard=True
        )
        await message.answer('Введите номер телефона пользователя, которому необходимо выдать права (номер телефона начинается без "8" и "+7")', reply_markup=back)
        await Admin.phone.set()
    else:
        await message.answer('У вас нет прав')

@dp.message_handler(state=Admin.phone)
async def set_by_phone(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    elif len(message.text) != 10:
        await message.answer("Неправильно введённый номнер", reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
    else:
        user = db.set_admin_by_phone(message.text)
        if user:
            await message.answer("Права назначены", reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        else:
            await message.answer("Пользователь не найден", reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
    await state.finish()

@dp.message_handler(commands=['upload'])
async def upload(message: types.Message):
    if db.user_is_admin(message.from_user.id):
        back = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="/back - назад")
                ]
            ],
            resize_keyboard=True
        )
        await message.answer('Отправьте документ', reply_markup=back)
        await NewTest.file.set()
    else:
        await message.answer('У вас нет прав')

@dp.message_handler(state=NewTest.file, content_types = ['document'])
async def answer_document_file(message: types.Message, state: FSMContext):
    directory = "files"
    files = os.listdir(directory)
    filename = message.document.file_name
    if files.count(filename) == 0:
        id_file = db.get_file_by_filename(filename)
        if not id_file:
            async with state.proxy() as data:
                data["filename"] = filename
                data["document_id"] = message.document.file_id
            await message.answer('Файл успешно получен\nВведите описание файла')
            await NewTest.next()
        else:
            await message.answer('Файл с таким именем уже существует в базе данных! Измените название файла', reply_markup = menu_admin if db.user_is_admin(message.from_user.id) else menu)
            await state.finish()
    else:
        await message.answer('Файл с таким именем уже существует в базе данных! Измените название файла', reply_markup = menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()

@dp.message_handler(state=NewTest.file)
async def exit_update(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()

@dp.message_handler(state=NewTest.description)
async def test_description(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        async with state.proxy() as data:
            data["description"] = message.text
        await message.answer('Введите первый вопрос')
        await NewTest.next()

async def add_question(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["questions"].append(message.text)
    await message.answer("Введите первый вариант ответа")

async def add_answer(message: types.Message, state: FSMContext, n, m, answer):
    async with state.proxy() as data:
        data["answers"][n][m] = message.text
    await message.answer(answer)

async def add_correct(message: types.Message, state: FSMContext, answer, correct):
    try:
        if 0 < int(message.text) < 5:
            async with state.proxy() as data:
                data["corrects"].append(int(message.text))
            await message.answer(answer)
            await NewTest.next()
        else:
            await message.answer("Введите корректный номер!")
            await message.answer("Введите номер правильного ответа (1-3)")
            await correct.set()
    except ValueError:
        await message.answer("Введите корректный номер!")
        await message.answer("Введите номер правильного ответа (1-3)")
        await correct.set()


@dp.message_handler(state=NewTest.question1)
async def question1(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        async with state.proxy() as data:
            data["questions"] = []
        await add_question(message, state)
        await NewTest.next()

@dp.message_handler(state=NewTest.answer11)
async def answer11(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        # Количество строк матрицы (количество вопросов)
        n = 4
        # Количество столбцов матрицы (количество ответов на каждый вопрос)
        m = 3
        async with state.proxy() as data:
            data["answers"] = [0] * n
            for i in range(n):
                data["answers"][i] = [0] * m
        await add_answer(message, state, 0, 0, "Введите второй вариант ответа")
        await NewTest.next()

@dp.message_handler(state=NewTest.answer12)
async def answer12(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        await add_answer(message, state, 0, 1, "Введите третий вариант ответа")
        await NewTest.next()

@dp.message_handler(state=NewTest.answer13)
async def answer13(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        await add_answer(message, state, 0, 2, "Введите номер правильного ответа")
        await NewTest.next()

@dp.message_handler(state=NewTest.correct1)
async def correct1(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        async with state.proxy() as data:
            data["corrects"] = []
        await add_correct(message, state, "Введите второй вопрос", NewTest.correct1)


@dp.message_handler(state=NewTest.question2)
async def question2(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        await add_question(message, state)
        await NewTest.next()

@dp.message_handler(state=NewTest.answer21)
async def answer21(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        await add_answer(message, state, 1, 0, "Введите второй вариант ответа")
        await NewTest.next()

@dp.message_handler(state=NewTest.answer22)
async def answer22(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        await add_answer(message, state, 1, 1, "Введите третий вариант ответа")
        await NewTest.next()

@dp.message_handler(state=NewTest.answer23)
async def answer23(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        await add_answer(message, state, 1, 2, "Введите номер правильного ответа")
        await NewTest.next()

@dp.message_handler(state=NewTest.correct2)
async def correct2(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        await add_correct(message, state, "Введите третий вопрос", NewTest.correct2)

@dp.message_handler(state=NewTest.question3)
async def question3(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        await add_question(message, state)
        await NewTest.next()

@dp.message_handler(state=NewTest.answer31)
async def answer31(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        await add_answer(message, state, 2, 0, "Введите второй вариант ответа")
        await NewTest.next()

@dp.message_handler(state=NewTest.answer32)
async def answer32(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        await add_answer(message, state, 2, 1, "Введите третий вариант ответа")
        await NewTest.next()

@dp.message_handler(state=NewTest.answer33)
async def answer33(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        await add_answer(message, state, 2, 2, "Введите номер правильного ответа")
        await NewTest.next()

@dp.message_handler(state=NewTest.correct3)
async def correct3(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        await add_correct(message, state, "Введите четвертый вопрос", NewTest.correct3)

@dp.message_handler(state=NewTest.question4)
async def question4(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        await add_question(message, state)
        await NewTest.next()

@dp.message_handler(state=NewTest.answer41)
async def answer41(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        await add_answer(message, state, 3, 0, "Введите второй вариант ответа")
        await NewTest.next()

@dp.message_handler(state=NewTest.answer42)
async def answer42(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        await add_answer(message, state, 3, 1, "Введите третий вариант ответа")
        await NewTest.next()

@dp.message_handler(state=NewTest.answer43)
async def answer43(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        await add_answer(message, state, 3, 2, "Введите номер правильного ответа")
        await NewTest.next()

@dp.message_handler(state=NewTest.correct4)
async def correct4(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup=menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        try:
            if 0 < int(message.text) < 5:
                async with state.proxy() as data:
                    data["corrects"].append(int(message.text))

                data = await state.get_data()

                """Заливаем файл"""
                global TOKEN
                file_info = await bot.get_file(data.get("document_id"))
                fi = file_info.file_path
                directory_files = os.path.join("files", data.get("filename"))
                urllib.request.urlretrieve(f'https://api.telegram.org/file/bot{TOKEN}/{fi}', f'./{directory_files}')
                db.add_file(data.get("filename"), data.get("description"))

                id_file = db.get_file_by_filename(data.get("filename"))[0]

                """Добавляем опросы в БД"""
                id_question = []
                for i in range(4):
                    id_question.append(db.add_question(id_file, data.get("questions")[i], data.get("corrects")[i]))
                    for j in range(3):
                        db.add_answer(int(id_question[i]), data.get("answers")[i][j])

                await message.answer("Опрос создан", reply_markup = menu_admin if db.user_is_admin(message.from_user.id) else menu)
                await state.finish()
                users = db.get_users()
                directory = os.path.join("files", data.get("filename"))
                for id in users:
                    if id[4] and id[5]:
                        try:
                            await bot.send_message(id[1], "Новый документ!")
                            with open(directory, "rb") as f:
                                await bot.send_document(id[1], f, caption="Описание:\n" + data.get("description"))
                        except Exception:
                            ban = open("users_which_banned_bot.txt", 'a')
                            ban.write("Пользователь {} заблокировал чат-бота".format(id[1]))
                            ban.close()
                            continue
            else:
                await message.answer("Введите корректный номер!")
                await message.answer("Введите номер правильного ответа (1-3)")
                await NewTest.correct4.set()
        except ValueError:
            await message.answer("Введите корректный номер!")
            await message.answer("Введите номер правильного ответа (1-3)")
            await NewTest.correct4.set()

@dp.message_handler(commands=['docs'])
async def docs(message: types.Message):
    docs = db.get_files()
    text = ""
    i = 1
    for d in docs:
        text += "<b>{}. {}</b>\n   ID: {}\n   Описание:\n   {}\n\n".format(str(i), d[1], str(d[0]), str(d[2]))
        i += 1
    if text:
        await message.answer(text, parse_mode="html")
    else:
        await message.answer("Документы отсутствуют", parse_mode="html")

@dp.message_handler(commands=['get_users'])
async def get_users(message: types.Message):
    if db.user_is_admin(message.from_user.id):
        users = db.get_users()
        text = ""
        for u in users:
            # Пользователи без номера телефона и ФИО не будут включены в список
            # Пользователи категории "Админ" не будут включены в список
            if u[4] and u[5] and not u[3]:
                # Phone
                text += "{} ({})\n".format(str(u[5]), str(u[4]))
        if text:
            await message.answer(text)
        else:
            await message.answer("Список пользователей отсутствует")
    else:
        await message.answer("У вас нет прав")

@dp.message_handler(commands=['myresults'])
async def myresults(message: types.Message):
    docs = db.get_tests_by_id_user(message.from_user.id, 1)
    text = "<b>Тесты, которые вы сдали:</b>\n"
    if docs:
        for d in docs:
            file = db.get_file_by_id(d[1])
            text += "   {} (ID: {}), использовано попыток: {}\n\n".format(file[1], str(d[1]), str(d[4]))
    else:
        text += "   Отсутствуют"
    text += "\n\n"
    docs = db.get_tests_by_id_user(message.from_user.id, 0)
    text += "<b>Тесты, которые вы не сдали:</b>\n"
    if docs:
        for d in docs:
            file = db.get_file_by_id(d[1])
            text += "   {} (ID: {}), использовано попыток: {}\n\n".format(file[1], str(d[1]), str(d[4]))
    else:
        text += "   Отсутствуют"
    await message.answer(text, parse_mode="html")

def set_borders(borders):
    borders.left = xlwt.Borders.THIN
    borders.right = xlwt.Borders.THIN
    borders.top = xlwt.Borders.THIN
    borders.bottom = xlwt.Borders.THIN
    return borders

def set_style(style, bold, align, borders):
    font0 = xlwt.Font()
    font0.bold = bold
    style.font = font0

    alignment = xlwt.Alignment()
    alignment.horz = align
    style.alignment = alignment

    if borders:
        borders = set_borders(xlwt.Borders())
        style.borders = borders

    return style

@dp.message_handler(commands=['results'])
async def results(message: types.Message):
    if db.user_is_admin(message.from_user.id):
        docs = db.get_files()
        if docs:
            book = xlwt.Workbook()
            styleDescr = set_style(xlwt.XFStyle(), True, xlwt.Alignment.HORZ_RIGHT, False)
            styleHeader = set_style(xlwt.XFStyle(), True, xlwt.Alignment.HORZ_CENTER, True)
            styleLeftData = set_style(xlwt.XFStyle(), False, xlwt.Alignment.HORZ_LEFT, True)
            styleRightData = set_style(xlwt.XFStyle(), False, xlwt.Alignment.HORZ_RIGHT, True)

            for d in docs:
                sheet = book.add_sheet(str(d[0]), cell_overwrite_ok=True)
                sheet.write(0, 1, 'По состоянию на:', styleDescr)
                sheet.write(0, 2, datetime.datetime.now().strftime("%d-%m-%Y %H:%M"))
                sheet.write(1, 1, 'Название:', styleDescr)
                sheet.write(1, 2, str(d[1]))
                sheet.write(2, 1, 'ID:', styleDescr)
                sheet.write(2, 2, str(d[0]))
                sheet.write(3, 1, 'Описание:', styleDescr)
                sheet.write(3, 2, str(d[2]))

                sheet.write_merge(5, 5, 1, 3, 'Сдали', styleHeader)
                sheet.write_merge(5, 5, 4, 6, 'Не сдали', styleHeader)
                sheet.write(6, 0, '№', styleHeader)
                sheet.write(6, 1, 'ФИО', styleHeader)
                sheet.write(6, 2, 'Номер телефона', styleHeader)
                sheet.write(6, 3, 'Попыток', styleHeader)
                sheet.write(6, 4, 'ФИО', styleHeader)
                sheet.write(6, 5, 'Номер телефона', styleHeader)
                sheet.write(6, 6, 'Попыток', styleHeader)
                solved_test = db.get_users_solved_test(d[0], 1)
                length_fullname = 3
                index_solved = 0
                for s in solved_test:
                    if not s[7]:
                        index_solved += 1
                        line = 6 + index_solved
                        fullname = str(s[5])
                        sheet.write(line, 0, str(index_solved), styleRightData)
                        sheet.write(line, 1, fullname, styleLeftData)
                        sheet.write(line, 2, str(s[6]), styleLeftData)
                        sheet.write(line, 3, str(s[4]), styleLeftData)
                        sheet.write(line, 4, "", styleLeftData)
                        sheet.write(line, 5, "", styleLeftData)
                        sheet.write(line, 6, "", styleLeftData)
                        length_fullname = max(length_fullname, len(fullname))
                sheet.col(1).width = 256 * (length_fullname + 3)
                sheet.col(2).width = 256 * (len('Номер телефона') + 3)

                solved_test = db.get_users_solved_test(d[0], 0)
                length_fullname = 3
                index_failed = 0
                for s in solved_test:
                    if not s[7]:
                        index_failed += 1
                        line = 6 + index_failed
                        fullname = str(s[5])
                        sheet.write(line, 0, str(index_failed), styleRightData)
                        if index_failed > index_solved:
                            sheet.write(line, 1, "", styleLeftData)
                            sheet.write(line, 2, "", styleLeftData)
                            sheet.write(line, 3, "", styleLeftData)
                        sheet.write(line, 4, fullname, styleLeftData)
                        sheet.write(line, 5, str(s[6]), styleLeftData)
                        sheet.write(line, 6, str(s[4]), styleLeftData)
                        length_fullname = max(length_fullname, len(fullname))
                sheet.col(4).width = 256 * (length_fullname + 3)
                sheet.col(5).width = 256 * (len('Номер телефона') + 3)
            book.save('results.xls')
            directory = "results.xls"
            with open(directory, "rb") as f:
                await bot.send_document(message.from_user.id, f)
        else:
            "Список тестов отсутствует"
    else:
        await message.answer("У вас нет прав")

@dp.message_handler(commands=['get_db'])
async def get_db(message: types.Message, state: FSMContext):
    if db.user_is_admin(message.from_user.id):
        directory = "db.db"
        with open(directory, "rb") as f:
            await bot.send_document(message.from_user.id, f)
    else:
        await message.answer("У вас нет прав")


@dp.message_handler(commands=['set_db'])
async def upload_db(message: types.Message):
    if db.user_is_admin(message.from_user.id):
        back = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="/back - назад")
                ]
            ],
            resize_keyboard=True
        )
        await message.answer('Отправьте файл с базой данных', reply_markup=back)
        await Database.file.set()
    else:
        await message.answer('У вас нет прав')

@dp.message_handler(state=Database.file, content_types = ['document'])
async def answer_document_file(message: types.Message, state: FSMContext):
    filename = message.document.file_name
    id_file = message.document.file_id
    if filename == "db.db":
        global TOKEN
        file_info = await bot.get_file(id_file)
        fi = file_info.file_path
        urllib.request.urlretrieve(f'https://api.telegram.org/file/bot{TOKEN}/{fi}', f'./{filename}')
        await bot.send_message(message.from_user.id, 'Файл успешно получен', reply_markup = menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        await message.answer('Данный файл не является файлом базы данных!', reply_markup = menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()

@dp.message_handler(state=Database.file, content_types = ['text'])
async def exit_upload_db(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup = menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()

@dp.message_handler(commands=['get'])
async def get(message: types.Message):
    docs = db.get_files()
    docs_list = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="/back - назад")
            ]
        ],
        resize_keyboard=True
    )
    for d in docs:
        docs_list.add(str(d[0]))
    await message.answer('Выберите ID документа', reply_markup=docs_list)
    await Files.id.set()

@dp.message_handler(state=Files.id)
async def getting(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup = menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        try:
            file = db.get_file_by_id(int(message.text))
            if file:
                directory = os.path.join("files", file[1])
                with open(directory, "rb") as f:
                    await bot.send_document(message.from_user.id, f, caption="Описание:\n" + file[2], reply_markup = menu_admin if db.user_is_admin(message.from_user.id) else menu)
                await state.finish()
            else:
                await message.answer("Документ не найден", reply_markup = menu_admin if db.user_is_admin(message.from_user.id) else menu)
                await state.finish()
        except ValueError:
            await message.answer("Введите корректное число")
            await message.answer('Введите ID документа')
            await Files.id.set()

@dp.message_handler(commands=['test'])
async def get(message: types.Message):
    id_user = message.from_user.id
    check_phone = db.check_phone(id_user)
    if check_phone:
        if check_phone[0]:
            if db.check_fullname(id_user)[0]:
                docs = db.get_files()
                docs_list = ReplyKeyboardMarkup(
                    keyboard=[
                        [
                            KeyboardButton(text="/back - назад")
                        ]
                    ],
                    resize_keyboard=True
                )
                for d in docs:
                    docs_list.add(str(d[0]))
                # await message.answer('На каждый вопрос из теста даётся 30 секунд. Если время истечет, система автоматически засчитает несдачу\n\n'
                #                      'Если вы считаете, что соединение с сетью Интернет не является стабильным на должном уровне, лучше отложите сдачу теста на другое время\n\n'
                #                      'В случае несдачи теста вы можете его перепройти. Максимальное количество попыток - 3\n\n'
                #                      'Введите ID документа', reply_markup=docs_list)
                await message.answer('В случае несдачи теста вы можете его перепройти. Максимальное количество попыток - 3\n\n'
                                    'Введите ID документа', reply_markup=docs_list)
                await Test.id.set()
            else:
                await message.answer('Вы не можете участвовать в прохождении теста, так как вы не указали ФИО\nДля этого введите /start')
        else:
            await message.answer('Вы не можете участвовать в прохождении теста, пока не дадите доступ к номеру телефона\nДля этого введите /start')
    else:
        await message.answer('Ошибка идентификации вашего профиля. Пожалуйста, введите команду /start')


def transpose(l1, l2):
    for i in range(len(l1[0])):
        row = []
        for item in l1:
            row.append(item[i])
        l2.append(row)
    return l2


@dp.message_handler(state=Test.id)
async def q1_test(message: types.Message, state: FSMContext):
    if message.text == "/back - назад":
        await message.answer('Отмена', reply_markup = menu_admin if db.user_is_admin(message.from_user.id) else menu)
        await state.finish()
    else:
        try:
            id_test = int(message.text)
            id_user = message.from_user.id
            questions = db.get_questions(id_test)
            if questions:
                users_test = db.check_users_test(id_test, id_user)
                attempts = 0
                status = 0
                if users_test:
                    attempts = users_test[0][4]
                    status = users_test[0][3]
                if attempts < 3 and status == 0:
                    async with state.proxy() as data:
                        data["time"] = time.time()
                        data["id_test"] = int(message.text)
                        data["id_question"], data["questions"], data["answers"] = [], [], []
                        data["score"] = 0
                    for q in questions:
                        async with state.proxy() as data:
                            data["id_question"].append(q[0])
                            data["questions"].append(q[2])
                    data = await state.get_data()
                    for id_question in data.get("id_question"):
                        answers = db.get_answers(id_question)
                        async with state.proxy() as data:
                            data["answers"].append(transpose(answers, []))
                    answers = ReplyKeyboardMarkup(
                        keyboard=[
                            [
                                KeyboardButton(text="1")
                            ],
                            [
                                KeyboardButton(text="2")
                            ],
                            [
                                KeyboardButton(text="3")
                            ]
                        ],
                        resize_keyboard=True
                    )
                    await message.answer("Количество использованных попыток: {} (максимум: 3)".format(str(attempts)), reply_markup=answers)
                    text = "<b>1) {}</b>\n\n".format(data.get("questions")[0])
                    for i in range(3):
                        text += "{}. {}\n".format(str(i+1), data.get("answers")[0][0][i])
                    await message.answer(text, parse_mode="html")
                    await Test.next()
                elif status == 1:
                    await message.answer("Вы уже сдали данный тест", reply_markup = menu_admin if db.user_is_admin(message.from_user.id) else menu)
                    await state.finish()
                else:
                    await message.answer("Вы не можете пройти тест, так как вы использовали 3 попытки", reply_markup = menu_admin if db.user_is_admin(message.from_user.id) else menu)
                    await state.finish()
            else:
                await message.answer("Тест не найден")
                await state.finish()
        except ValueError:
            await message.answer("Введите корректный ID")
            await message.answer('Введите ID документа')
            await Test.id.set()

async def check_questions(message: types.Message, state: FSMContext, question, index_question):
    data = await state.get_data()
    id_test = data.get("id_test")
    id_user = message.from_user.id
    users_test = db.check_users_test(id_test, id_user)
    """Убран таймер"""
    # if time.time() - data.get("time") <= 30:
    try:
        answer = int(message.text)
        if 0 < answer < 4:
            if db.check_answer(data.get("id_question")[index_question - 1], answer):
                await message.answer("Правильно!")
                async with state.proxy() as data:
                    data["score"] += 1
            else:
                await message.answer("Неверный ответ!")
            async with state.proxy() as data:
                data["time"] = time.time()
            text = "<b>{}) {}</b>\n\n".format(index_question + 1, data.get("questions")[index_question])

            for i in range(3):
                text += "{}. {}\n".format(str(i+1), data.get("answers")[index_question][0][i])
            await message.answer(text, parse_mode="html")
            await Test.next()
        else:
            await message.answer("Введите корректный ответ (1-3)")
            await question.set()
    except ValueError:
        await message.answer("Введите корректный ответ (1-3)")
        await question.set()
    # else:
    #     await message.answer("Истекло время на ответ. Тест не сдан", reply_markup = menu_admin if db.user_is_admin(id_user) else menu)
    #     db.change_users_test(id_test, id_user, 0, users_test[0][4] + 1)
    #     await state.finish()

@dp.message_handler(state=Test.question1)
async def q2_test(message: types.Message, state: FSMContext):
    await check_questions(message, state, Test.question1, 1)

@dp.message_handler(state=Test.question2)
async def q3_test(message: types.Message, state: FSMContext):
    await check_questions(message, state, Test.question2, 2)

@dp.message_handler(state=Test.question3)
async def q3_test(message: types.Message, state: FSMContext):
    await check_questions(message, state, Test.question2, 3)

@dp.message_handler(state=Test.question4)
async def test_results(message: types.Message, state: FSMContext):
    data = await state.get_data()
    id_test = data.get("id_test")
    id_user = message.from_user.id
    # if time.time() - data.get("time") <= 30:
    try:
        data = await state.get_data()
        answer = int(message.text)
        if 0 < answer < 4:
            if db.check_answer(data.get("id_question")[3], answer):
                await message.answer("Правильно!")
                async with state.proxy() as data:
                    data["score"] += 1
            else:
                await message.answer("Неверный ответ!")
            if not db.check_users_test(id_test, id_user):
                db.set_users_test(id_test, id_user)
            users_test = db.check_users_test(id_test, id_user)
            status = 0
            if data.get("score") == 4:
                status = 1
                await message.answer("Тест сдан", reply_markup = menu_admin if db.user_is_admin(id_user) else menu)
            else:
                await message.answer("Тест не сдан", reply_markup = menu_admin if db.user_is_admin(id_user) else menu)
            db.change_users_test(id_test, id_user, status, users_test[0][4] + 1)
            await state.finish()
        else:
            await message.answer("Введите корректный ответ (1-3)")
            await Test.question4.set()
    except ValueError:
        await message.answer("Введите корректный ответ (1-3)")
        await Test.question4.set()
    # else:
    #     await message.answer("Истекло время на ответ. Тест не сдан", reply_markup = menu_admin if db.user_is_admin(id_user) else menu)
    #     db.change_users_test(id_test, id_user, 0, users_test[0][4] + 1)
    #     await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)