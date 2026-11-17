import sqlite3
from datetime import date


class Database:
    def __init__(self, db_name="habits.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY(habit_id) REFERENCES habits(id)
            )
        ''')

        self.conn.commit()

    def add_habit(self, name: str):
        self.cursor.execute(
            'INSERT INTO habits (name, created_at) VALUES (?, ?)',
            (name, date.today().isoformat())
        )
        self.conn.commit()

    def get_all_habits(self):
        self.cursor.execute('SELECT id, name FROM habits ORDER BY id')
        return self.cursor.fetchall()

    def is_completed(self, habit_id: int):
        today = date.today().isoformat()

        self.cursor.execute(
            'SELECT id FROM completions WHERE habit_id = ? AND date = ?',
            (habit_id, today)
        )

        return self.cursor.fetchone() is not None

    
    def get_streak(self, habit_id: int):
        """Считает текущую серию дней подряд"""
        self.cursor.execute(
            'SELECT date FROM completions WHERE habit_id = ? ORDER BY date DESC',
            (habit_id,)
        )
        dates = [row[0] for row in self.cursor.fetchall()]
        
        if not dates:
            return 0
        
        streak = 0
        current_date = date.today()
        
        for date_str in dates:
            expected_date = current_date.isoformat()
            if date_str == expected_date:
                streak += 1
                current_date = date.fromisoformat(date_str)
                from datetime import timedelta
                current_date -= timedelta(days=1)
            else:
                break
        
        return streak

    def get_best_streak(self, habit_id: int):
        """Считает рекордную серию дней"""
        self.cursor.execute(
            'SELECT date FROM completions WHERE habit_id = ? ORDER BY date ASC',
            (habit_id,)
        )
        dates = [row[0] for row in self.cursor.fetchall()]
        
        if not dates:
            return 0
        
        best_streak = 0
        current_streak = 1
        
        for i in range(1, len(dates)):
            prev_date = date.fromisoformat(dates[i-1])
            curr_date = date.fromisoformat(dates[i])
            
            from datetime import timedelta
            if (curr_date - prev_date).days == 1:
                current_streak += 1
            else:
                best_streak = max(best_streak, current_streak)
                current_streak = 1
        
        best_streak = max(best_streak, current_streak)
        return best_streak

    def toggle_completion(self, habit_id: int):
        today = date.today().isoformat()

        self.cursor.execute(
            'SELECT id FROM completions WHERE habit_id = ? AND date = ?',
            (habit_id, today)
        )

        result = self.cursor.fetchone()

        if result:
            self.cursor.execute(
                'DELETE FROM completions WHERE habit_id = ? AND date = ?',
                (habit_id, today)
            )
        else:
            self.cursor.execute(
                'INSERT INTO completions (habit_id, date) VALUES (?, ?)',
                (habit_id, today)
            )

        self.conn.commit()

    def get_completions_for_month(self, habit_id: int):
        """Возвращает словарь {дата: True} с выполнениями за последние 30 дней"""
        from datetime import timedelta
        today = date.today()
        start_date = today - timedelta(days=29)  # 30 дней включая сегодня

        self.cursor.execute(
            'SELECT date FROM completions WHERE habit_id = ? AND date >= ?',
            (habit_id, start_date.isoformat())
        )

        # Преобразуем список дат в словарь для быстрого поиска
        return {row[0]: True for row in self.cursor.fetchall()}

    def delete_habit(self, habit_id: int):
        """Удаляет привычку и все связанные записи о выполнении"""
        # Сначала удаляем историю выполнений (чтобы не было "висячих" записей)
        self.cursor.execute(
            'DELETE FROM completions WHERE habit_id = ?',
            (habit_id,)
        )
        # Затем удаляем саму привычку
        self.cursor.execute(
            'DELETE FROM habits WHERE id = ?',
            (habit_id,)
        )
        self.conn.commit()
        
    def close(self):
        self.conn.close()