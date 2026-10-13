# Development log
# October 12 2026 7:11pm CDT - Session 1 start

I reviewed the project instructions and rubric. I plan to use the supplied Python implementation as a reference and work through it in stages.
Today I will review the three-program design and integrate the logger. My main question before coding is how the logger will know when to stop reading messages from the driver’s pipe.

The driver will start two child processes. The logger will read action and message lines from standard input and write timestamped records to a file.
I will test multiple words in a message, QUIT, and appending to an existing file. I also need to check the separate Git/Project Instructions PDF.



# 10-12-2026 7:45pm CDT - Session 1 end

I reviewed and integrated the supplied logger code. The first test wrote two timestamped records. QUIT stopped the logger, so neither QUIT nor the following IGNORE message appeared. 
The second run appended a third record without removing the first two.

The test command first failed because PowerShell does not include printf. Then python3 failed because Windows could not find Python under that command. 
Using a PowerShell string array and the python command resolved both issues.

The logger reads messages from standard input. Later, the driver will send those messages through a pipe. 
The logger flushes each record so it does not remain buffered until exit. Next session I will review and test the encryption backend.