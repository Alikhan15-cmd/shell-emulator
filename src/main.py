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
            self.username = os.getlogin()
        except Exception:
            self.username = "user"

        hostname = socket.gethostname()
        self.root.title(f"Эмулятор [{self.username}@{hostname}]")

        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=20)
        self.text_area.pack(padx=10, pady=10)

        self.entry = tk.Entry(root, width=80)
        self.entry.pack(padx=10, pady=10)
        self.entry.bind("<Return>", self.process_input)

        self.vfs = {}
        self.current_path = "/"
        self.load_vfs()
        self.run_startup_script()

    def load_vfs(self):
        vfs_real_path = self.config.get('vfs_path', '')
        if not vfs_real_path or not os.path.exists(vfs_real_path):
            self.display_text("Предупреждение: Папка VFS не найдена!")
            return

        self.vfs["/"] = {"type": "dir", "content": []}

        for root, dirs, files in os.walk(vfs_real_path):
            rel_path = os.path.relpath(root, vfs_real_path)
            vfs_path = "/" if rel_path == "." else "/" + rel_path.replace("\\", "/")

            if vfs_path not in self.vfs:
                self.vfs[vfs_path] = {"type": "dir", "content": []}

            for d in dirs:
                if d not in self.vfs[vfs_path]["content"]:
                    self.vfs[vfs_path]["content"].append(d)

            for f in files:
                if f not in self.vfs[vfs_path]["content"]:
                    self.vfs[vfs_path]["content"].append(f)
                file_real_path = os.path.join(root, f)
                file_vfs_path = vfs_path + ("" if vfs_path == "/" else "/") + f

                try:
                    with open(file_real_path, 'r', encoding='utf-8') as file_obj:
                        content = file_obj.read()
                except Exception:
                    content = ""

                self.vfs[file_vfs_path] = {"type": "file", "content": content}

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
                    if not self.execute_command(command):
                        self.display_text("Ошибка в скрипте! Остановка.")
                        break

    def process_input(self, event):
        command_line = self.entry.get()
        self.display_text(f"> {command_line}")
        self.entry.delete(0, tk.END)
        self.execute_command(command_line)

    def get_absolute_path(self, path):
        if path.startswith("/"):
            return path
        if self.current_path == "/":
            return "/" + path
        return self.current_path + "/" + path

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
            items = self.vfs.get(self.current_path, {}).get("content", [])
            self.display_text("  ".join(items) if items else "(пусто)")
            return True

        elif cmd == "cd":
            if len(args) < 2:
                self.current_path = "/"
                return True
            target = args[1]
            if target == "..":
                if self.current_path != "/":
                    self.current_path = "/".join(self.current_path.split("/")[:-1]) or "/"
                return True

            new_path = self.get_absolute_path(target)
            if new_path in self.vfs and self.vfs[new_path]["type"] == "dir":
                self.current_path = new_path
            else:
                self.display_text(f"cd: {target}: Нет такой папки")
            return True

        elif cmd == "whoami":
            self.display_text(self.username)
            return True

        elif cmd == "wc":
            if len(args) < 2:
                self.display_text("wc: укажите файл")
                return False
            file_path = self.get_absolute_path(args[1])
            if file_path in self.vfs and self.vfs[file_path]["type"] == "file":
                content = self.vfs[file_path]["content"]
                lines = len(content.split('\n'))
                words = len(content.split())
                chars = len(content)
                self.display_text(f"{lines} {words} {chars} {args[1]}")
            else:
                self.display_text(f"wc: {args[1]}: Файл не найден")
            return True

        elif cmd == "uniq":
            if len(args) < 2:
                self.display_text("uniq: укажите файл")
                return False
            file_path = self.get_absolute_path(args[1])
            if file_path in self.vfs and self.vfs[file_path]["type"] == "file":
                lines = self.vfs[file_path]["content"].split('\n')
                result = []
                for line in lines:
                    if not result or result[-1] != line:
                        result.append(line)
                self.display_text("\n".join(result))
            else:
                self.display_text(f"uniq: {args[1]}: Файл не найден")
            return True

        elif cmd == "cp":  # Команда копирования файлов в памяти
            if len(args) < 3:
                self.display_text("cp: укажите исходный файл и файл назначения")
                return False
            src = self.get_absolute_path(args[1])
            dst = self.get_absolute_path(args[2])

            if src not in self.vfs or self.vfs[src]["type"] != "file":
                self.display_text(f"cp: {args[1]}: Нет такого файла")
                return False

            # Копируем файл в виртуальной памяти
            self.vfs[dst] = {"type": "file", "content": self.vfs[src]["content"]}

            # Добавляем имя нового файла в папку, чтобы команда ls его видела
            parent_dir = "/".join(dst.split("/")[:-1]) or "/"
            file_name = dst.split("/")[-1]

            if parent_dir in self.vfs and self.vfs[parent_dir]["type"] == "dir":
                if file_name not in self.vfs[parent_dir]["content"]:
                    self.vfs[parent_dir]["content"].append(file_name)
            return True

        else:
            self.display_text(f"{cmd}: команда не найдена")
            return False


def load_settings():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vfs', help='Путь к VFS')
    parser.add_argument('--script', help='Путь к стартовому скрипту')
    parser.add_argument('--config', default='config.toml')
    args = parser.parse_args()

    config_data = {}
    if os.path.exists(args.config):
        with open(args.config, "rb") as f:
            config_data = tomllib.load(f)

    if args.vfs: config_data['vfs_path'] = args.vfs
    if args.script: config_data['script_path'] = args.script
    return config_data


if __name__ == "__main__":
    settings = load_settings()
    root = tk.Tk()
    app = EmulatorGUI(root, settings)
    root.mainloop()