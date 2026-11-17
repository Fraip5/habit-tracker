import tkinter as tk
from datetime import date, timedelta
import customtkinter as ctk
from database import Database


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class HabitTrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.db = Database()

        self.title("Habit Tracker")
        self.geometry("600x500")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.title_label = ctk.CTkLabel(
            self,
            text="Трекер привычек",
            font=ctk.CTkFont(size=26, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=20)

        self.add_frame = ctk.CTkFrame(self)
        self.add_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.add_frame.grid_columnconfigure(0, weight=1)

        self.habit_entry = ctk.CTkEntry(
            self.add_frame,
            placeholder_text="Введите новую привычку..."
        )
        self.habit_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.add_button = ctk.CTkButton(
            self.add_frame,
            text="Добавить",
            command=self.add_habit
        )
        self.add_button.grid(row=0, column=1, padx=10, pady=10)

        self.habits_frame = ctk.CTkScrollableFrame(self)
        self.habits_frame.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")
        self.habits_frame.grid_columnconfigure(0, weight=1)

        self.refresh_habits()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def add_habit(self):
        name = self.habit_entry.get().strip()

        if not name:
            from tkinter import messagebox
            messagebox.showwarning(
                "Ошибка",
                "Введите название привычки!\n\nПоле не может быть пустым."
            )
            return

        self.db.add_habit(name)
        self.habit_entry.delete(0, tk.END)
        self.refresh_habits()

    def refresh_habits(self):
        # Удаляем все старые элементы
        for widget in self.habits_frame.winfo_children():
            widget.destroy()

        habits = self.db.get_all_habits()

        if not habits:
            empty_label = ctk.CTkLabel(
                self.habits_frame,
                text="Пока нет привычек. Добавьте первую."
            )
            empty_label.grid(row=0, column=0, padx=10, pady=10)
            return

        for index, habit in enumerate(habits):
            habit_id = habit[0]
            habit_name = habit[1]

            # Блок с привычкой (рамка)
            habit_card = ctk.CTkFrame(self.habits_frame)
            habit_card.grid(row=index, column=0, padx=10, pady=10, sticky="ew")
            habit_card.grid_columnconfigure(0, weight=1)

            # Строка с чекбоксом и счётчиками
            top_row = ctk.CTkFrame(habit_card, fg_color="transparent")
            top_row.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
            top_row.grid_columnconfigure(1, weight=1)

            streak = self.db.get_streak(habit_id)
            best_streak = self.db.get_best_streak(habit_id)
            text = f"{habit_name}  🔥 {streak}  🏆 {best_streak}"

            checkbox_var = tk.BooleanVar(value=self.db.is_completed(habit_id))
            checkbox = ctk.CTkCheckBox(
                top_row,
                text=text,
                variable=checkbox_var,
                command=lambda h_id=habit_id: self.toggle_habit(h_id),
                font=ctk.CTkFont(size=16)
            )
            checkbox.grid(row=0, column=0, columnspan=2, sticky="w")

                        # Кнопка удаления
            delete_button = ctk.CTkButton(
                top_row,
                text="🗑",
                width=40,
                fg_color="#d32f2f",       # Красный цвет
                hover_color="#b71c1c",    # Тёмно-красный при наведении
                command=lambda h_id=habit_id, h_name=habit_name: self.delete_habit(h_id, h_name)
            )
            delete_button.grid(row=0, column=2, padx=5)

            # Мини-календарь (heatmap) — 30 дней, 5 строк по 6 дней
            calendar_frame = ctk.CTkFrame(habit_card, fg_color="transparent")
            calendar_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")

            completions = self.db.get_completions_for_month(habit_id)

            from datetime import timedelta
            today = date.today()

            for day_offset in range(30):
                current_day = today - timedelta(days=29 - day_offset)
                day_str = current_day.isoformat()

                # Определяем цвет: зелёный если выполнена, серый если нет
                if day_str in completions:
                    color = "#2ea043"  # зелёный
                else:
                    color = "#2d2d2d"  # тёмно-серый

                # Позиция в сетке: строка и столбец
                row = day_offset // 6
                col = day_offset % 6

                square = ctk.CTkLabel(
                    calendar_frame,
                    text="",
                    width=18,
                    height=18,
                    fg_color=color,
                    corner_radius=3
                )
                square.grid(row=row, column=col, padx=2, pady=2)

    def toggle_habit(self, habit_id):
        self.db.toggle_completion(habit_id)
        self.refresh_habits()

    def delete_habit(self, habit_id, habit_name):
        """Показывает окно подтверждения и удаляет привычку"""
        from tkinter import messagebox
        
        confirm = messagebox.askyesno(
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить привычку «{habit_name}»?\n\nВся история выполнений будет безвозвратно удалена."
        )
        
        if confirm:
            self.db.delete_habit(habit_id)
            self.refresh_habits()

    def on_close(self):
        self.db.close()
        self.destroy()


if __name__ == "__main__":
    app = HabitTrackerApp()
    app.mainloop()