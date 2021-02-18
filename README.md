# Instruction Bot

### Описание
Instruction Bot выполнен по заказу помощника машиниста Дальневосточной дирекции
моторвагонного подвижного состава (Демченко А.Б.).

Цель: упрощение системы тестирования сотрудников ОАО "РЖД".

Instruction Bot - это бот в приложении Telegram, написанный на языке программирования
Python.
***
### Способы взаимодействия
#### Обычный пользователь

Может смотреть список выложенных документов и проходить тест по каждому из них.
Имеет доступ к просмотру собственных результатов сдачи теста, а также количество использованных попыток сдачи теста.

#### Администратор
Имеет те же возможности, что и  обычный пользователь. Дополнительно имеет доступ к списку всех пользователей,
результатов сдачи каждого теста. Может загружать в Базу Данных (далее - БД) файлы и создавать опросы к ним.
Имеет привилегии выдачи прав администратора пользователям. Имеет доступ к файлу БД, может путем загрузки заменять файл БД на сервере.
***
### Тест
Тест представляет собой набор вопросов и ответов к нему. На данный момент на каждый файл
можно создать ровно 3 вопроса и 4 варианта ответов на каждый из них.

Доступ к решению теста имеет любой зарегистрированный пользователь, предоставивший боту личный номер телефона.
Количество попыток на решение теста: 3.

##### Доступ к решению теста запрещается, если:
1. Пользователь исчерпал количество попыток на решение теста.
2. Пользователь успешно решил тест.

***

### Начать диалог с ботом

1. Перейти по ссылке: https://t.me/RZD_instruction_bot
2. Нажать кнопку "START"
3. Следуя инструкциям бота, предоставить личный номер телефона

***

### Список команд

/help - посмотреть список доступных команд в приложении Telegram

/docs - список документов

/get - получить файл документа

/test - пройти тест

/myresults - посмотреть собственные результаты сдачи тестов

#### Для администраторов:
/get_users - получить список пользователей

/upload - загрузить документ и создать опрос к нему

/results - результаты сдачи тестов сотрудниками

/get_db - получить файл базы данных

/set_db - отправить файл базы данных

/admin - выдать права администратора пользователю

***

### Описание файлов и каталогов:

#### /files/

Содержит файлы, по которым имеются опросы.

#### /reserve/

Директория, в котором расположены резервные файлы БД на случай утраты или поломки основного.

#### db.db

Файл БД, в котором хранится информация о пользователях, файлах и тестах.

#### main.py

В файле содержится код взаимодействия пользователя с ботом

#### sql_requests.py

В файле содержится код SQL-запросов к БД.

#### states.py

Набор классов, в каждом из которых прописаны [механизмы конечных автоматов состояний](https://docs.aiogram.dev/en/latest/migration_1_to_2.html#states-group).

#### config.py

Скрытый файл, отстутствующий в репозитории. Содержит класс Config(), хранящий токен бота. Имеет метод-геттер getToken(), возвращающий токен. Обращение к классу происходит из файла main.py.

#### requirements.txt

Хранит информацию о модулях, использованных в проекте.
