import os
import socket
import shlex
import argparse
import tkinter as tk
from tkinter import scrolledtext
import tomllib


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

        # 1. Загружаем файлы в память при запуске[cite: 9]
        self.vfs = {}  # Здесь будем хранить всю виртуальную файловую систему
        self.current_path = "/"  # Мы всегда начинаем работу в корневой папке (обозначается как "/")
        self.load_vfs()

        self.run_startup_script()

    def load_vfs(self):
        # Эта функция читает реальную директорию на диске пользователя и загружает её в память[cite: 9]
        vfs_real_path = self.config.get('vfs_path', '')
        if not vfs_real_path or not os.path.exists(vfs_real_path):
            self.display_text("Предупреждение: Папка VFS не найдена!")
            return

        # Создаем корень
        self.vfs["/"] = {"type": "dir", "content": []}

        for root, dirs, files in os.walk(vfs_real_path):
            # Вычисляем путь внутри эмулятора
            rel_path = os.path.relpath(root, vfs_real_path)
            vfs_path = "/" if rel_path == "." else "/" + rel_path.replace("\\", "/")

            if vfs_path not in self.vfs:
                self.vfs[vfs_path] = {"type": "dir", "content": []}

            # Запоминаем папки
            for d in dirs:
                self.vfs[vfs_path]["content"].append(d)

            # Запоминаем файлы и их содержимое в память, чтобы потом не трогать диск[cite: 9]
            for f in files:
                self.vfs[vfs_path]["content"].append(f)
                file_real_path = os.path.join(root, f)
                file_vfs_path = vfs_path + ("" if vfs_path == "/" else "/") + f

                try:
                    with open(file_real_path, 'r', encoding='utf-8') as file_obj:
                        content = file_obj.read()
                except Exception:
                    content = "<содержимое файла>"

                self.vfs[file_vfs_path] = {"type": "file", "content": content}

        self.display_text("VFS успешно загружена в память!")

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
                    self.display_text(f"> {command}")
                    success = self.execute_command(command)
                    if not success:
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
        elif cmd == "ls":
            # Теперь ls по-настоящему выводит список файлов из памяти![cite: 9]
            items = self.vfs.get(self.current_path, {}).get("content", [])
            self.display_text("  ".join(items) if items else "(пусто)")
            return True
        elif cmd == "cd":
            self.display_text(f"Вызвана команда-заглушка: cd, аргументы: {args[1:]}")
            return True
        else:
            self.display_text(f"{cmd}: команда не найдена")
            return False


def load_settings():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vfs', help='Путь к VFS')
    parser.add_argument('--script', help='Путь к стартовому скрипту')
    parser.add_argument('--config', help='Путь к конфигурационному файлу TOML', default='config.toml')
    args = parser.parse_args()

    config_data = {}
    if os.path.exists(args.config):
        with open(args.config, "rb") as f:
            config_data = tomllib.load(f)

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