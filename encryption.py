#!/usr/bin/env python3
"""Line-based Vigenere service; only this process owns the current passkey."""

import re
import sys


def letters_only(text):
    return re.fullmatch(r"[A-Za-z]+", text) is not None


def transform(text, key, decrypt=False):
    direction = -1 if decrypt else 1
    result = []
    for index, letter in enumerate(text):
        value = ord(letter) - ord("A")
        shift = ord(key[index % len(key)]) - ord("A")
        result.append(chr(ord("A") + (value + direction * shift) % 26))
    return "".join(result)


def main():
    key = None
    for line in sys.stdin:
        parts = line.rstrip("\r\n").split(maxsplit=1)
        if not parts:
            print("ERROR Missing command", flush=True)
            continue
        command = parts[0].upper()
        argument = parts[1] if len(parts) == 2 else ""
        if command == "QUIT":
            return 0
        if command not in {"PASS", "ENCRYPT", "DECRYPT"}:
            print("ERROR Unknown command", flush=True)
            continue
        if not letters_only(argument):
            print("ERROR Input must contain only letters A-Z", flush=True)
            continue
        argument = argument.upper()
        if command == "PASS":
            key = argument
            print("RESULT", flush=True)
        elif key is None:
            print("ERROR Password not set", flush=True)
        else:
            result = transform(argument, key, decrypt=command == "DECRYPT")
            print(f"RESULT {result}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
