# Development log
# 10-12-2026 6:41pm CDT - Session 1 start

I reviewed the project instructions and rubric. I plan to use the supplied Python implementation as a reference and work through it in stages.
Today I will review the three-program design and integrate the logger. My main question before coding is how the logger will know when to stop reading messages from the driver’s pipe.

The driver will start two child processes. The logger will read action and message lines from standard input and write timestamped records to a file.
I will test multiple words in a message, QUIT, and appending to an existing file. I also need to check the separate Git/Project Instructions PDF.



# 10-12-2026 7:28 pm CDT - Session 1 end

I reviewed and integrated the supplied logger code. The first test wrote two timestamped records. QUIT stopped the logger, so neither QUIT nor the following IGNORE message appeared. 
The second run appended a third record without removing the first two.

The test command first failed because PowerShell does not include printf. Then python3 failed because Windows could not find Python under that command. 
Using a PowerShell string array and the python command resolved both issues.

The logger reads messages from standard input. Later, the driver will send those messages through a pipe. 
The logger flushes each record so it does not remain buffered until exit. Next session I will review and test the encryption backend.


# 10-13-2026 11:10pm CDT - Session 2 start

Since the last session, I researched about some question i had about the logger and
protocol. Today I will review and integrate the encryption backend.
I will check the supplied HELLO example and a longer repeating-key example.

The backend keeps its passkey in its own process memory. PASS changes that
key. ENCRYPT and DECRYPT each return one line that starts with RESULT or
ERROR. I will check missing keys, invalid strings, and alphabet wraparound.


# 10-13-2026 11:55pm CDT - Session 2 end

I integrated the supplied encryption.py and tested its commands. With the key LEMON, encrypting ATTACKATDAWN returned LXFOPVEFRNHR. 
Decrypting that result returned ATTACKATDAWN. With the key B, encrypting Z returned A, which confirmed that the cipher wraps around the alphabet.

PASS 123 returned an error because the key must contain only letters. Encrypting Z again still returned A. 
This showed that rejecting an invalid password did not replace the existing key. These checks matched the expected output.

The key repeats when the text is longer than the key. Encryption adds the key shift, and decryption subtracts it, both modulo 26. 
The encryption process stores the current passkey in its own memory. Each response is flushed so the driver can read it through a pipe without waiting for the backend to exit. 
Next session I will connect both child programs to the interactive driver.


# 10-15-2026 4:01pm CDT - Session 3 start

The backend tests showed that encryption, decryption, and invalid-key handling work. My next question is how the driver will send commands through pipes and read each response without getting stuck waiting. Today I will review and integrate the suplied driver, connect it to both child programs, and test history selection and input validation.

Popen starts separate processes. The driver writes a newline-terminated command to the encryption child's stdin, flushes it, and reads one response line from its stdout. It sends log messages through the logger's stdin. I will check that new passwords stay out of history and logs, that history selections work, and that QUIT shuts down both child processes.


# 10-15-2026 4:49pm CDT - Session 3 end

I integrated the supplied driver and tested communication with both child programs. Encrypting ATTACKATDAWN with LEMON returned LXFOPVEFRNHR. Selecting that result from history for decryption returned ATTACKATDAWN. The log recorded startup, commands, results, and exit without including LEMON. A new run started with empty history and no password set.

I tested input validation and history controls. Hello World! and 123 were rejected, while lowercase hello was accepted. With key B, it returned IFMMP. An invalid history number was rejected, and entering 0 let me enter a new password. With key C, encrypting HELLO from history returned JGNNQ. Cancelling an encrypt command also worked.

The launch command initially failed because Windows could not find python3. Using python resolved it. The driver sends commands through pipes and flushes each message before reading a response. History stays in the driver, while the encryption process stores the passkey. Next session I will run the full test suite and check the repository for submission.



# 10-17-2026 1:11pm CDT - Session 4 start

The driver passed the manual checks in the last session. I still need to check how it handles unexpected input ending and file errors, and whether both child processes shut down cleanly. Today I will inspect the supplied tests, run them on my machine, review the run instructions, and check the Git repository before packaging it.

I will focus on child process launches, end-of-file shutdown, password values staying out of logs, invalid file paths, and history resetting between runs. I will also verify that the source files and devlog are tracked, the working tree is clean, and the submission ZIP includes the hidden .git directory so the commit history is preserved.


# 10-17-2026 1:47pm CDT - Session 4 end

I ran the supplied test suite on Windows. The first run passed 22 tests and failed the child-process launch check. The test assumed subprocess arguments were a list, but Windows provided a string. With assistance, I updated the test to handle both formats. All 23 tests then passed.

The manual Ctrl+C check exposed a shutdown problem. The interrupt reached both children, causing tracebacks and stopping the logger before it could record the driver's exit. I updated the driver to start the children in separate process groups on Windows, allowing the driver to handle Ctrl+C and send QUIT through the pipes.

After the changes, all 23 tests passed again. Ctrl+C exited without tracebacks, and the log recorded the shutdown request and driver exit. I also resolved a PowerShell copy-command error by copying the two files separately. Next I will finish reviewing the README, check that all source files and devlog changes are committed, and verify the submission ZIP includes the Git history.