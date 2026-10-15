#!/usr/bin/env python3
"""Launch two child programs and communicate with them using subprocess pipes."""

from pathlib import Path
import re
import subprocess
import sys


def send_line(stream, line):
    stream.write(line + "\n")
    stream.flush()


def read_letters(prompt, log):
    while True:
        text = input(prompt)
        if re.fullmatch(r"[A-Za-z]+", text):
            return text.upper()
        message = "Input must contain only letters A-Z (no spaces or symbols)."
        print("ERROR " + message)
        log("ERROR", message)


def show_history(history):
    if not history:
        print("History is empty.")
    for number, text in enumerate(history, start=1):
        print(f"{number}. {text}")


def choose_text(history, log, password=False):
    """Return (text, was_new), or None when the user cancels."""
    while True:
        choice = input("Use [n]ew text or [h]istory? (0 cancels): ").strip().lower()
        if choice == "0":
            return None
        if choice in {"n", "new", "1"}:
            return read_letters("Password: " if password else "Text: ", log), True
        if choice not in {"h", "history", "2"}:
            print("ERROR Choose n, h, or 0.")
            log("ERROR", "Choose n, h, or 0.")
            continue
        if not history:
            print("History is empty. Enter a new string.")
            return read_letters("Password: " if password else "Text: ", log), True
        show_history(history)
        while True:
            selected = input("History number (0 enters new text): ").strip()
            if selected == "0":
                return read_letters("Password: " if password else "Text: ", log), True
            if selected.isascii() and selected.isdigit():
                # Bound the digit count before conversion, even for malicious input.
                if len(selected) <= len(str(len(history))) + 1:
                    number = int(selected)
                    if 1 <= number <= len(history):
                        return history[number - 1], False
            print("ERROR Choose a listed history number or 0.")
            log("ERROR", "Choose a listed history number or 0.")


def stop_child(process):
    """Request normal exit, close pipe ends, and reap the child process."""
    if process is None:
        return True
    try:
        if process.poll() is None:
            send_line(process.stdin, "QUIT")
    except (BrokenPipeError, OSError):
        pass
    finally:
        if process.stdin is not None:
            try:
                process.stdin.close()
            except OSError:
                pass
    try:
        returncode = process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        print("ERROR A child process did not stop after QUIT.", file=sys.stderr)
        returncode = 1
    if process.stdout is not None:
        process.stdout.close()
    return returncode == 0


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 driver.py LOGFILE", file=sys.stderr)
        return 1
    directory = Path(__file__).resolve().parent
    logger = None
    encryption = None
    status = 0
    started = False
    history = []

    def log(action, message):
        send_line(logger.stdin, f"{action} {message}")

    try:
        # stderr stays separate from stdout, so errors cannot corrupt the protocol.
        logger = subprocess.Popen(
            [sys.executable, str(directory / "logger.py"), sys.argv[1]],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
            encoding="utf-8", bufsize=1,
        )
        encryption = subprocess.Popen(
            [sys.executable, str(directory / "encryption.py")],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
            encoding="utf-8", bufsize=1,
        )
        log("START", "Driver started.")
        started = True
        print("Commands: password, encrypt, decrypt, history, quit")
        while True:
            command = input("Command: ").strip().lower()
            if command not in {"password", "encrypt", "decrypt", "history", "quit"}:
                log("COMMAND", "Unknown command.")
                print("ERROR Unknown command.")
                log("ERROR", "Unknown command.")
                continue
            log("COMMAND", command)
            if command == "quit":
                log("RESULT", "Quit requested.")
                break
            if command == "history":
                show_history(history)
                log("RESULT", f"Displayed history ({len(history)} entries).")
                continue
            selection = choose_text(history, log, password=command == "password")
            if selection is None:
                print("Command cancelled.")
                log("RESULT", f"{command} cancelled.")
                continue
            text, was_new = selection
            if command == "password":
                # Neither the request nor the response log includes the passkey.
                request = "PASS " + text
            else:
                if was_new:
                    history.append(text)
                request = command.upper() + " " + text
                log("INPUT", text)
            send_line(encryption.stdin, request)
            response = encryption.stdout.readline()
            if not response:
                raise RuntimeError("Encryption process closed its output pipe.")
            parts = response.rstrip("\r\n").split(maxsplit=1)
            if not parts or parts[0] not in {"RESULT", "ERROR"}:
                raise RuntimeError("Encryption process returned an invalid response.")
            response_type = parts[0]
            result = parts[1] if len(parts) == 2 else ""
            if command == "password":
                message = "Password set." if response_type == "RESULT" else "Password rejected."
            else:
                message = result
                if response_type == "RESULT":
                    history.append(result)
            print(f"{response_type} {message}")
            log(response_type, message)
    except (EOFError, KeyboardInterrupt):
        print("\nInput ended. Shutting down.")
        if started:
            try:
                log("COMMAND", "quit (input ended)")
                log("RESULT", "Shutdown requested.")
            except OSError:
                status = 1
    except (OSError, RuntimeError) as error:
        print(f"ERROR {error}", file=sys.stderr)
        status = 1
        if started:
            try:
                log("ERROR", "Process communication failed.")
            except OSError:
                pass
    finally:
        if not stop_child(encryption):
            status = 1
        if started:
            try:
                log("EXIT", "Driver stopped.")
            except OSError:
                status = 1
        if not stop_child(logger):
            print("ERROR Logger failed; check the log file path.", file=sys.stderr)
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
