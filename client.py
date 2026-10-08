import socket
import threading
import protocol as proto

HOST = "127.0.0.1"
PORT = 5555


def listen_loop(sock, stop_event):
    while not stop_event.is_set():
        try:
            msg = proto.recv_message(sock)
        except (ConnectionResetError, OSError):
            msg = None

        if msg is None:
            print("\n[!] соединение с сервером потеряно")
            stop_event.set()
            break

        command, payload = msg
        text = payload.decode(
            "utf-8",
            errors="replace"
        )

        if command == "LIST":
            print(f"\n{ text }\n> ", end="")
        elif command == "ERRO":
            print(f"\n[ошибка] {text}\n> ", end="")
        else:
            print(f"\n{text}\n> ", end="")


def main():
    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    try:
        sock.connect((HOST, PORT))
    except (ConnectionRefusedError, OSError) as e:
        print(f"Не удалось подключиться: {e}")
        return

    stop_event = threading.Event()

    threading.Thread(
        target=listen_loop,
        args=(sock, stop_event),
        daemon=True
    ).start()

    print("Подключение установлено.")
    print("Команды:")
    print("/add <text>    - добавить задачу")
    print("/list           - показать задачи")
    print("/done <number>  - отметить задачу выполненной")
    print("/delete <number> - удалить задачу")
    print("/quit           - выйти")

    try:
        while not stop_event.is_set():
            line = input("> ").strip()

            if line == "/quit":
                proto.send_message(sock, "QUIT")
                break

            elif line.startswith("/add "):
                task_text = line[5:].strip()

                if not task_text:
                    print("Ошибка: укажите текст задачи.")
                    continue

                proto.send_message(
                    sock,
                    "ADD",
                    task_text.encode("utf-8")
                )

            elif line == "/add":
                print("Ошибка: используйте /add <текст>")

            elif line == "/list":
                proto.send_message(sock, "LIST")

            elif line.startswith("/done "):
                number = line[6:].strip()

                proto.send_message(
                    sock,
                    "DONE",
                    number.encode("utf-8")
                )

            elif line == "/done":
                print("Ошибка: используйте /done <номер>")

            elif line.startswith("/delete "):
                number = line[8:].strip()

                proto.send_message(
                    sock,
                    "DELETE",
                    number.encode("utf-8")
                )

            elif line == "/delete":
                print("Ошибка: используйте /delete <номер>")

            elif line:
                print("Неизвестная команда.")

    except (
        EOFError,
        KeyboardInterrupt,
        BrokenPipeError,
        OSError
    ):
        pass

    finally:
        stop_event.set()
        sock.close()


if __name__ == "__main__":
    main()
