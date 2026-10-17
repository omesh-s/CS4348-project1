#!/usr/bin/env python3
"""Black-box tests of actual programs, pipes, logs, and interactive workflows."""

from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent


def run(program, commands="", args=(), cwd=None):
    return subprocess.run(
        [sys.executable, str(ROOT / program), *map(str, args)],
        input=commands, capture_output=True, text=True, encoding="utf-8",
        timeout=10, cwd=cwd,
    )


class EncryptionTests(unittest.TestCase):
    def replies(self, commands):
        result = run("encryption.py", commands)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.splitlines()

    def test_missing_password(self):
        self.assertEqual(self.replies("ENCRYPT HELLO\nDECRYPT HELLO\nQUIT\n"),
                         ["ERROR Password not set"] * 2)

    def test_assignment_example(self):
        self.assertEqual(self.replies("PASS HELLO\nENCRYPT HELLO\nDECRYPT OIWWC\nQUIT\n"),
                         ["RESULT", "RESULT OIWWC", "RESULT HELLO"])

    def test_standard_vector(self):
        self.assertEqual(self.replies("PASS LEMON\nENCRYPT ATTACKATDAWN\nDECRYPT LXFOPVEFRNHR\n"),
                         ["RESULT", "RESULT LXFOPVEFRNHR", "RESULT ATTACKATDAWN"])

    def test_lowercase_and_key_replacement(self):
        self.assertEqual(self.replies("pass b\nencrypt z\nPASS C\nENCRYPT Z\nDECRYPT B\n"),
                         ["RESULT", "RESULT A", "RESULT", "RESULT B", "RESULT Z"])

    def test_invalid_inputs_do_not_replace_key(self):
        commands = "PASS B\nPASS 123\nENCRYPT Hi!\nDECRYPT A B\nPASS\nENCRYPT\nENCRYPT Z\n"
        replies = self.replies(commands)
        self.assertEqual(replies[0], "RESULT")
        self.assertTrue(all(x.startswith("ERROR ") for x in replies[1:-1]))
        self.assertEqual(replies[-1], "RESULT A")

    def test_unknown_blank_and_unicode(self):
        replies = self.replies("\nWHAT\nPASS café\n")
        self.assertTrue(all(x.startswith("ERROR ") for x in replies))
        self.assertEqual(len(replies), 3)

    def test_quit_stops_processing(self):
        self.assertEqual(self.replies("QUIT\nPASS HELLO\n"), [])

    def test_alphabet_wraparound_and_repeated_key(self):
        self.assertEqual(self.replies("PASS Z\nENCRYPT ABCXYZ\nDECRYPT ZABWXY\n"),
                         ["RESULT", "RESULT ZABWXY", "RESULT ABCXYZ"])


class LoggerTests(unittest.TestCase):
    def test_format_split_and_quit(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "activity.log"
            result = run("logger.py", "START Logging Started.\n\nEVENT several words\nSOLO\nQUIT\nIGNORE no\n", [path])
            self.assertEqual(result.returncode, 0, result.stderr)
            lines = path.read_text().splitlines()
            self.assertEqual(len(lines), 3)
            self.assertRegex(lines[0], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2} \[START\] Logging Started\.$")
            self.assertTrue(lines[1].endswith("[EVENT] several words"))
            self.assertTrue(lines[2].endswith("[SOLO] "))

    def test_append_and_eof(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "activity.log"
            for message in ["START first\n", "EXIT second\n"]:
                self.assertEqual(run("logger.py", message, [path]).returncode, 0)
            self.assertEqual(len(path.read_text().splitlines()), 2)

    def test_bad_path_and_missing_argument(self):
        self.assertNotEqual(run("logger.py").returncode, 0)
        with tempfile.TemporaryDirectory() as temp:
            self.assertNotEqual(run("logger.py", args=[Path(temp) / "missing" / "log"]).returncode, 0)


class DriverTests(unittest.TestCase):
    def session(self, commands, cwd=None):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "activity.log"
            result = run("driver.py", commands, [path], cwd=cwd)
            self.assertEqual(result.returncode, 0, result.stderr)
            return result.stdout, path.read_text()

    def test_full_workflow_and_password_redaction(self):
        out, log = self.session("PaSsWoRd\nn\nLeMoN\nEnCrYpT\nn\nAttackAtDawn\ndecrypt\nh\n2\nhistory\nquit\n")
        self.assertIn("RESULT LXFOPVEFRNHR", out)
        self.assertIn("RESULT ATTACKATDAWN", out)
        self.assertIn("3. ATTACKATDAWN", out)
        self.assertNotIn("LEMON", out + log)
        self.assertIn("[START] Driver started.", log)
        self.assertIn("[EXIT] Driver stopped.", log)
        self.assertIn("[COMMAND] password", log)
        self.assertIn("[RESULT] Password set.", log)
        self.assertEqual(len(re.findall(r"\[COMMAND\]", log)), 5)

    def test_error_input_remains_in_history(self):
        out, log = self.session("encrypt\nn\nHELLO\nhistory\nquit\n")
        self.assertIn("ERROR Password not set", out)
        self.assertIn("1. HELLO", out)
        self.assertNotIn("2. HELLO", out)
        self.assertIn("[ERROR] Password not set", log)

    def test_invalid_text_and_password_are_reprompted(self):
        out, log = self.session("password\nn\nkey123\nSECRET\nencrypt\nn\nHello World!\ncafé\n\nhello\nquit\n")
        self.assertEqual(out.count("ERROR Input must contain only letters"), 4)
        self.assertIn("RESULT Password set.", out)
        self.assertNotIn("SECRET", out + log)
        self.assertNotIn("key123", log)
        self.assertEqual(log.count("[ERROR] Input must contain only letters"), 4)

    def test_history_escape_and_bad_selection(self):
        out, _ = self.session("encrypt\nn\nHELLO\npassword\nh\n99\nabc\n0\nB\nencrypt\nx\nh\n1\nquit\n")
        self.assertIn("RESULT IFMMP", out)
        self.assertEqual(out.count("ERROR Choose a listed history number"), 2)
        self.assertIn("ERROR Choose n, h, or 0.", out)

    def test_history_password_not_added_or_logged(self):
        out, log = self.session("encrypt\nn\nHELLO\npassword\nh\n1\nhistory\nencrypt\nh\n1\nquit\n")
        self.assertIn("RESULT OIWWC", out)
        self.assertNotIn("2. HELLO", out)
        # HELLO was already logged as encryption input, but never as a PASS value.
        self.assertNotIn("PASS HELLO", log)

    def test_empty_history_falls_back_to_new(self):
        out, _ = self.session("history\npassword\nh\nB\nencrypt\nh\nA\nquit\n")
        self.assertIn("History is empty.", out)
        self.assertIn("RESULT B", out)

    def test_cancel_unknown_and_eof(self):
        out, log = self.session("nonsense\nencrypt\n0\n")
        self.assertIn("ERROR Unknown command.", out)
        self.assertIn("Command cancelled.", out)
        self.assertIn("[RESULT] encrypt cancelled.", log)
        self.assertIn("[EXIT] Driver stopped.", log)

    def test_eof_in_password_prompt(self):
        out, log = self.session("password\nn\n")
        self.assertIn("Input ended.", out)
        self.assertIn("[EXIT] Driver stopped.", log)

    def test_history_resets_between_runs(self):
        self.session("encrypt\nn\nHELLO\nquit\n")
        out, _ = self.session("history\nquit\n")
        self.assertIn("History is empty.", out)
        self.assertNotIn("1. HELLO", out)

    def test_launch_from_another_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            out, _ = self.session("quit\n", cwd=temp)
            self.assertIn("Commands:", out)

    def test_bad_log_path_and_missing_argument(self):
        self.assertNotEqual(run("driver.py").returncode, 0)
        with tempfile.TemporaryDirectory() as temp:
            result = run("driver.py", "quit\n", [Path(temp) / "missing" / "log"])
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ERROR", result.stderr)

    def test_two_child_launches_and_clean_shutdown(self):
        with tempfile.TemporaryDirectory() as temp:
            wrapper = Path(temp) / "observe.py"
            log_path = Path(temp) / "log"
            wrapper.write_text(
                "import runpy, subprocess, sys\n"
                "def audit(event, args):\n"
                "    if event == 'subprocess.Popen':\n"
                "        command = args[1]\n"
                "        if not isinstance(command, str):\n"
                "            command = subprocess.list2cmdline(command)\n"
                "        print('CHILD ' + command, file=sys.stderr, flush=True)\n"
                "sys.addaudithook(audit)\n"
                "sys.argv = sys.argv[1:]\n"
                "runpy.run_path(sys.argv[0], run_name='__main__')\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(wrapper), str(ROOT / "driver.py"), str(log_path)],
                input="quit\n", capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            children = [
                line for line in result.stderr.splitlines()
                if line.startswith("CHILD ")
            ]
            expected_commands = [
                [sys.executable, str(ROOT / "logger.py"), str(log_path)],
                [sys.executable, str(ROOT / "encryption.py")],
            ]
            self.assertEqual(
                children,
                ["CHILD " + subprocess.list2cmdline(command)
                    for command in expected_commands],
            )
            self.assertNotIn("ERROR", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
