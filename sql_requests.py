import sqlite3

class Requests:
    def __init__(self, database_file):
        """Подключаемся к БД и сохраняем курсор соединения"""
        self.connection = sqlite3.connect(database_file)
        self.cursor = self.connection.cursor()

    def get_users(self):
        with self.connection:
            return self.cursor.execute("SELECT * FROM `users` ORDER BY `fullname`").fetchall()

    def get_user_by_id(self, id_user):
        with self.connection:
            return self.cursor.execute("SELECT * FROM `users` WHERE id_telegram = ?", (id_user,)).fetchone()

    """Оператор 'LIKE' в данной функции использован по причине того, что номер телефона в таблице БД может начинаться как с '7', так и с '+7'.
    Чтобы избежать путаницы, пользователю предлагается не вводить код страны. В файле main.py до вызова данной функции существует проверка, чтобы длина строки phone был равен 10,
    во избежание инъекций"""
    def set_admin_by_phone(self, phone):
        with self.connection:
            self.cursor.execute(
                "UPDATE `users` SET "
                "`admin` = ? WHERE "
                "`phone` LIKE ?",
                (1, "%" + phone)
            ).fetchall()
            return self.cursor.execute("SELECT `username` FROM `users` WHERE phone LIKE ?", ("%" + phone,)).fetchone()

    def add_user(self, id_user, username):
        with self.connection:
            return self.cursor.execute("INSERT INTO `users` (`id_telegram`, `username`, `admin`) VALUES (?, ?, ?)", (id_user, username, 0))

    def set_phone(self, id_user, phone):
        with self.connection:
            return self.cursor.execute(
                "UPDATE `users` SET "
                "`phone` = ? WHERE "
                "`id_telegram` = ?",
                (phone, id_user,)
            )

    def user_exists(self, id_user):
        with self.connection:
            return self.cursor.execute("SELECT * FROM `users` WHERE id_telegram = ?", (id_user,)).fetchone()

    def check_phone(self, id_user):
        with self.connection:
            return self.cursor.execute("SELECT `phone` FROM `users` WHERE id_telegram = ?", (id_user,)).fetchone()

    def check_fullname(self, id_user):
        with self.connection:
            return self.cursor.execute("SELECT `fullname` FROM `users` WHERE id_telegram = ?", (id_user,)).fetchone()

    def set_fullname(self, id_user, fullname):
        with self.connection:
            return self.cursor.execute(
                "UPDATE `users` SET "
                "`fullname` = ? WHERE "
                "`id_telegram` = ?",
                (fullname, id_user,)
            )

    def user_is_admin(self, id_user):
        with self.connection:
            return self.cursor.execute("SELECT * FROM `users` WHERE id_telegram = ? AND admin = ?", (id_user, 1)).fetchone()

    def get_files(self):
        with self.connection:
            return self.cursor.execute("SELECT * FROM `files`").fetchall()

    def add_file(self, filename, description):
        with self.connection:
            return self.cursor.execute("INSERT INTO `files` (`filename`, `description`) VALUES (?, ?)", (filename, description,))

    def get_file_by_filename(self, filename):
        with self.connection:
            return self.cursor.execute("SELECT `id` FROM `files` WHERE filename = ?", (filename,)).fetchone()

    def get_file_by_id(self, id_file):
        with self.connection:
            return self.cursor.execute("SELECT * FROM `files` WHERE `id` = ?", (id_file,)).fetchone()

    def add_question(self, id_file, question, correct):
        with self.connection:
            self.cursor.execute(
                "INSERT INTO `questions` "
                "(`id_file`, `question`, `correct`) VALUES "
                "(?, ?, ?)",
                (id_file, question, correct,)
            )
            return self.cursor.lastrowid

    def get_questions(self, id_test):
        with self.connection:
            return self.cursor.execute("SELECT * FROM `questions` WHERE `id_file` = ?", (id_test,)).fetchall()

    def add_answer(self, id_question, answer):
        with self.connection:
            self.cursor.execute(
                "INSERT INTO `answers` "
                "(`id_question`, `answer`) VALUES "
                "(?, ?)",
                (id_question, answer,)
            )

    def get_answers(self, id_question):
        with self.connection:
            return self.cursor.execute("SELECT `answer` FROM `answers` WHERE `id_question` = ?", (id_question,)).fetchall()

    def check_answer(self, id_question, answer):
        with self.connection:
            row = self.cursor.execute("SELECT * FROM `questions` WHERE `id` = ?", (id_question,)).fetchall()
            return bool(row[0][3] == answer)

    """Данная функция проверяет, решал ли ранее данный тест пользователь"""
    def check_users_test(self, id_test, id_user):
        with self.connection:
            return self.cursor.execute("SELECT * FROM `solve_test` WHERE `id_test` = ? AND `id_user` = ?", (id_test, id_user)).fetchall()

    """Данная функция проверяет не только сам факт решения теста пользователем, но и с каким результатом он его решил"""
    def get_tests_by_id_user(self, id_user, is_passed):
        with self.connection:
            return self.cursor.execute("SELECT * FROM `solve_test` WHERE `id_user` = ? AND `is_passed` = ?", (id_user, is_passed)).fetchall()

    def set_users_test(self, id_test, id_user):
        with self.connection:
            return self.cursor.execute(
                "INSERT INTO `solve_test` "
                "(`id_test`, `id_user`) VALUES "
                "(?, ?)",
                (id_test, id_user,)
            )

    def change_users_test(self, id_test, id_user, is_passed, attempt):
        with self.connection:
            return self.cursor.execute(
                "UPDATE `solve_test` SET "
                "`is_passed` = ?, `attempt` = ? WHERE "
                "`id_test` = ? AND `id_user` = ?",
                (is_passed, attempt, id_test, id_user,)
            )

    def get_users_solved_test(self, id_test, is_passed):
        return self.cursor.execute("SELECT solve_test.id, solve_test.id_test, solve_test.id_user, solve_test.is_passed, solve_test.attempt, users.fullname, users.phone, users.admin "
                                    "FROM users INNER JOIN solve_test ON users.id_telegram = solve_test.id_user WHERE `id_test` = ? AND `is_passed` = ? ORDER BY fullname ASC",
                                    (id_test, is_passed)
                                   ).fetchall()
        # return self.cursor.execute("SELECT id, id_test FROM `solve_test` WHERE `id_test` = ? AND `is_passed` = ?",
        #                            (id_test, is_passed)).fetchall()