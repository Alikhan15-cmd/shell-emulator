import os
import socket
import shlex
import argparse
import tkinter as tk
from tkinter import scrolledtext
import tomllib  # Специальная библиотека для чтения TOML файлов


class EmulatorGUI:
    def __init__(self, root, config_data):
        self.root = root
        self.config = config_data

        try:
            username = os.getlogin()
        except Exception:
            username = "user"
        hostname = socket.gethostname()
        self.root.title(f"Эмулятор [{username}@{hostname}]")

        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=20)
        self.text_area.pack(padx=10, pady=10)

        self.entry = tk.Entry(root, width=80)
        self.entry.pack(padx=10, pady=10)
        self.entry.bind("<Return>", self.process_input)

        # 1. Отладочный вывод настроек при запуске[cite: 8]
        self.display_text("--- Запуск эмулятора: Отладочный вывод ---")
        self.display_text(f"Путь к VFS: {self.config.get('vfs_path', 'Не задан')}")
        self.display_text(f"Стартовый скрипт: {self.config.get('script_path', 'Не задан')}")
        self.display_text("--------------------------------------------\n")

        # 2. Выполняем стартовый скрипт, если он есть[cite: 9]
        self.run_startup_script()

    def display_text(self, text):
        self.text_area.insert(tk.END, text + "\n")
        self.text_area.see(tk.END)

    def run_startup_script(self):
        script_path = self.config.get('script_path')
        if script_path and os.path.exists(script_path):
            with open(script_path, 'r', encoding='utf-8') as file:
                for line in file:
                    command = line.strip()
                    if not command:
                        continue
                    # Имитируем ввод пользователя[cite: 9]
                    self.display_text(f"> {command}")
                    success = self.execute_command(command)
                    if not success:
                        # Останавливаемся при первой же ошибке[cite: 9]
                        self.display_text("Ошибка во время исполнения стартового скрипта! Остановка.")
                        break

    def process_input(self, event):
        command_line = self.entry.get()
        self.display_text(f"> {command_line}")
        self.entry.delete(0, tk.END)
        self.execute_command(command_line)

    def execute_command(self, command_line):
        if not command_line.strip():
            return True

        try:
            args = shlex.split(command_line)
        except ValueError as e:
            self.display_text(f"Ошибка ввода: {e}")
            return False

        cmd = args[0]

        if cmd == "exit":
            self.root.destroy()
            return True
        elif cmd in ["ls", "cd"]:
            self.display_text(f"Вызвана команда: {cmd}, аргументы: {args[1:]}")
            return True
        else:
            self.display_text(f"{cmd}: команда не найдена")
            return False


def load_settings():
    # Настраиваем чтение параметров из командной строки[cite: 8]
    parser = argparse.ArgumentParser()
    parser.add_argument('--vfs', help='Путь к VFS')
    parser.add_argument('--script', help='Путь к стартовому скрипту')
    parser.add_argument('--config', help='Путь к конфигурационному файлу TOML', default='config.toml')
    args = parser.parse_args()

    config_data = {}

    # Читаем конфигурационный файл[cite: 8]
    if os.path.exists(args.config):
        with open(args.config, "rb") as f:
            config_data = tomllib.load(f)

    # Приоритет командной строки над файлом[cite: 9]
    if args.vfs:
        config_data['vfs_path'] = args.vfs
    if args.script:
        config_data['script_path'] = args.script

    return config_data


if __name__ == "__main__":
    settings = load_settings()
    root = tk.Tk()
    app = EmulatorGUI(root, settings)
    root.mainloop()