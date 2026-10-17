# CS 4348 Project 1: processes, pipes, and encryption

## Run

Use Python 3. No third-party packages or compilation are needed.

```bash
python3 driver.py activity.log
```

Keep `driver.py`, `logger.py`, and `encryption.py` in the same directory.
The log file path is relative to the directory where you run the command.
The driver locates child scripts relative to its own file, so it also works
when launched from a different directory.

## Menu

Enter one command at a time: `password`, `encrypt`, `decrypt`, `history`, or `quit`.
For password/encrypt/decrypt, choose `n` for new text or `h` for history.
Use a numbered history entry to select it. At the history prompt, `0` switches
to new text. At the new/history prompt, `0` cancels the current command.
If history is empty, choosing it falls back to a new text prompt.

Strings must contain one or more ASCII letters A-Z. Spaces, digits, punctuation,
and empty input are rejected. The driver converts valid strings to uppercase.
Commands are case insensitive.

New encryption/decryption input and successful results enter history.
Choosing an existing input does not add another copy of that input, though
its successful result is added. New passwords do not enter history. History
exists only in driver memory and resets on every run.

## Programs and protocol

`driver.py` starts exactly two child programs using `subprocess.Popen`.
Both have piped standard input and output. The driver writes log records to
the logger's stdin. Logger stdout is connected but has no normal output.
The driver writes backend commands to encryption stdin and reads one response
line from encryption stdout. Child stderr stays separate from the protocol.

Every message ends in a newline. The sender flushes its output before the
receiver waits for a line. Each process has its own memory: only the driver
owns history, and only the encryption process keeps the current passkey.

`encryption.py` accepts `PASS key`, `ENCRYPT text`, `DECRYPT text`, and `QUIT`.
PASS returns `RESULT`; encrypt/decrypt return `RESULT text` or `ERROR message`.
QUIT exits without a reply. The service also validates standalone input and
handles end-of-file.

For letters represented as 0 through 25, encryption uses `(text + key) % 26`
and decryption uses `(text - key) % 26`. Key characters repeat using
`index % len(key)`. For example, HELLO with key HELLO becomes OIWWC.

`logger.py LOGFILE` reads `ACTION message` lines and appends records in this format:

```text
YYYY-MM-DD HH:MM [ACTION] message
```

It uses the computer's local time in 24-hour format and flushes each record.
QUIT ends logging and is not written as a record.

The driver logs startup, each menu command, encryption/decryption input,
command results, and exit. PASS arguments and new password values are not
written to the log. A string already in encryption history can later be used
as a password; its earlier use remains in the history/log, as required.

The driver sends QUIT to both children, closes pipe handles, and waits for
both to exit. EOF and Ctrl+C also trigger cleanup. A failed child or invalid
log path produces a nonzero exit status. Timeouts prevent cleanup from hanging.

## Test

```bash
python3 -m unittest -v test_project
```

Tests run the programs as real processes and use temporary log files.
They cover known cipher vectors, wraparound, validation, passkey changes,
logging, history, password redaction, cancellation, EOF, bad paths, execution
from another directory, and two actual child launches followed by shutdown.

## Development records

`devlog.md` must contain the student's own entries made during real work
sessions. Include it and all source files in Git from the first session.
The final submission ZIP must include the repository's `.git` directory.
Do not submit generated logs, cache folders, or the reference-kit folders.
