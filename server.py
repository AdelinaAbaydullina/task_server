import socket
import threading
import protocol as proto

HOST = "0.0.0.0"
PORT = 5555

# Общий список задач для всех клиентов.
tasks = []

# Блокировка для безопасного доступа к общему списку.
tasks_lock = threading.Lock()


def send_error(sock, message):
    proto.send_message(
        sock,
        "ERRO",
        message.encode("utf-8")
    )


def format_tasks():
    with tasks_lock:
        if not tasks:
            return "Список задач пуст."

        result = []

        for number, task in enumerate(tasks, start=1):
            mark = "x" if task["done"] else " "
            result.append(
                f"{number}. [{mark}] {task['text']}"
            )

        return "\n".join(result)


def handle_client(sock, addr):
    print(f"[+] Подключился клиент {addr}")

    try:
        while True:
            msg = proto.recv_message(sock)

            if msg is None:
                print(f"[-] Клиент {addr} отключился")
                break

            command, payload = msg
            text = payload.decode(
                "utf-8",
                errors="replace"
            ).strip()

            if command == "ADD":
                if not text:
                    send_error(
                        sock,
                        "Использование: /add <текст>"
                    )
                    continue

                with tasks_lock:
                    tasks.append({
                        "text": text,
                        "done": False
                    })
                    number = len(tasks)

                proto.send_message(
                    sock,
                    "TEXT",
                    (
                        f"Задача добавлена: "
                        f"{number}. [ ] {text}"
                    ).encode("utf-8")
                )

            elif command == "LIST":
                result = format_tasks()

                proto.send_message(
                    sock,
                    "LIST",
                    result.encode("utf-8")
                )

            elif command == "DONE":
                if not text:
                    send_error(
                        sock,
                        "Использование: /done <номер>"
                    )
                    continue

                try:
                    number = int(text)
                except ValueError:
                    send_error(
                        sock,
                        "Номер задачи должен быть числом."
                    )
                    continue

                with tasks_lock:
                    if number < 1 or number > len(tasks):
                        send_error(
                            sock,
                            "Задачи с таким номером не существует."
                        )
                        continue

                    tasks[number - 1]["done"] = True
                    task_text = tasks[number - 1]["text"]

                proto.send_message(
                    sock,
                    "TEXT",
                    (
                        f"Задача выполнена: "
                        f"{number}. [x] {task_text}"
                    ).encode("utf-8")
                )

            elif command == "DELETE":
                if not text:
                    send_error(
                        sock,
                        "Использование: /delete <номер>"
                    )
                    continue

                try:
                    number = int(text)
                except ValueError:
                    send_error(
                        sock,
                        "Номер задачи должен быть числом."
                    )
                    continue

                with tasks_lock:
                    if number < 1 or number > len(tasks):
                        send_error(
                            sock,
                            "Задачи с таким номером не существует."
                        )
                        continue

                    deleted = tasks.pop(number - 1)

                proto.send_message(
                    sock,
                    "TEXT",
                    (
                        f"Задача удалена: "
                        f"{deleted['text']}"
                    ).encode("utf-8")
                )

            elif command == "QUIT":
                proto.send_message(
                    sock,
                    "TEXT",
                    "Работа завершена. До свидания!".encode("utf-8")
                )
                print(f"[-] Клиент {addr} вышел")
                break

            else:
                send_error(
                    sock,
                    f"Неизвестная команда: {command}"
                )

    except (ConnectionResetError, BrokenPipeError, OSError) as e:
        print(f"[!] Клиент {addr}: соединение закрыто ({e})")

    finally:
        sock.close()


def main():
    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    ) as server:

        server.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        server.bind((HOST, PORT))
        server.listen()

        print(f"[*] Сервер слушает {HOST}:{PORT}")
        print("[*] Ожидание клиентов...")

        while True:
            client_sock, addr = server.accept()

            threading.Thread(
                target=handle_client,
                args=(client_sock, addr),
                daemon=True
            ).start()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] Сервер остановлен")
