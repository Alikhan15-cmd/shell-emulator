import os
import socket
import shlex
import tkinter as tk
from tkinter import scrolledtext


class EmulatorGUI:
    def __init__(self, root):
        self.root = root

        # Получаем настоящее имя пользователя и имя компьютера
        try:
            username = os.getlogin()
        except Exception:
            username = "user"
        hostname = socket.gethostname()

        # Делаем правильный заголовок окна по заданию
        self.root.title(f"Эмулятор [{username}@{hostname}]")

        # Создаем большое текстовое поле для вывода
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=20)
        self.text_area.pack(padx=10, pady=10)

        # Создаем маленькое поле внизу для ввода команд
        self.entry = tk.Entry(root, width=80)
        self.entry.pack(padx=10, pady=10)
        self.entry.bind("<Return>", self.process_command)  # Команда запускается по нажатию Enter

        self.display_text("Добро пожаловать в эмулятор! Введите команду (например, ls 'моя папка' или exit).")

    def display_text(self, text):
        # Эта функция просто печатает текст на экран
        self.text_area.insert(tk.END, text + "\n")
        self.text_area.see(tk.END)

    def process_command(self, event):
        # Получаем текст, который ввел пользователь
        command_line = self.entry.get()
        self.display_text(f"> {command_line}")
        self.entry.delete(0, tk.END)  # Очищаем поле ввода

        if not command_line.strip():
            return

        try:
            # shlex.split правильно разбивает текст на слова и понимает текст в кавычках
            args = shlex.split(command_line)
        except ValueError as e:
            self.display_text(f"Ошибка ввода: {e}")
            return

        cmd = args[0]

        # Проверяем команды
        if cmd == "exit":
            # Настоящая команда выхода
            self.root.destroy()
        elif cmd in ["ls", "cd"]:
            # Команды-заглушки: они пока просто пишут свое имя и переданные слова[cite: 8]
            self.display_text(f"Вызвана команда: {cmd}, аргументы: {args[1:]}")
        else:
            self.display_text(f"{cmd}: команда не найдена")


if __name__ == "__main__":
    # Запускаем графическое окно[cite: 8]
    root = tk.Tk()
    app = EmulatorGUI(root)
    root.mainloop()