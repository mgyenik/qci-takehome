# Installation and Use
## Dependencies
This take home project uses pip to manage dependencies. It is recommended to
create a virtualenv to not clutter your environment while running it. The only
dependency other than python itself is aiohttp and its dependencies though, so if
you have that installed or prefer not to use virtualenvs, you can just install
probably any version of aiohttp through pip and skip this.

Using python's built in pip and virtualenv requires __python version 3.4 or
later__.

To create a virtualenv and install the dependencies into it using pip, run the
following:

```shell
# Create and activate virtualenv
...$ python3 -m venv takehome-env
...$ source takehome-env/bin/activate

# Install dependencies into virtualenv with pip
(takehome-env) ...$ python3 -m pip install -r requirements.txt 
```

That should be all that's needed to run the project!

## Running
The project comes with a simple `run.sh` script which will run both the server
and sender using sane default arguments. Files are created in `/tmp`, and
messages are printed to stdout instead of logged to a file. A succesful run will
print messages from both the sender and the server, and terminate gracefully
like so:

```shell
(takehome-env) ...$ sh run.sh 
======== Running on http://127.0.0.1:8000 ========
(Press CTRL+C to quit)
[SENDER][INFO][2022-04-01 18:23:02,025] - Generated new blob of length 318116
[SENDER][INFO][2022-04-01 18:23:02,026] - W0 wrote binary file to /tmp/sender-94afe877-4c65-4124-ab2f-64918fdcb3b8.bin
[SERVER][INFO][2022-04-01 18:23:02,030] - Wrote a 318116 byte file to /tmp/server-94afe877-4c65-4124-ab2f-64918fdcb3b8.bin
[SENDER][INFO][2022-04-01 18:23:02,030] - W0 successfully sent blob and received response Successfully received the 318116 byte file
[SENDER][INFO][2022-04-01 18:23:02,367] - Generated new blob of length 665348
[SENDER][INFO][2022-04-01 18:23:02,376] - W1 wrote binary file to /tmp/sender-884cf2ab-b8f8-487b-80f2-bee91794ee5d.bin
[SERVER][INFO][2022-04-01 18:23:02,387] - Wrote a 665348 byte file to /tmp/server-884cf2ab-b8f8-487b-80f2-bee91794ee5d.bin
[SENDER][INFO][2022-04-01 18:23:02,388] - W1 successfully sent blob and received response Successfully received the 665348 byte file
[SENDER][INFO][2022-04-01 18:23:03,258] - Generated new blob of length 988666
...
lots of logs
...
[SERVER][INFO][2022-04-01 18:23:48,215] - Wrote a 1043702 byte file to /tmp/server-67739ddb-2473-4bce-977f-de15aa1bde14.bin
[SENDER][INFO][2022-04-01 18:23:48,215] - W9 successfully sent blob and received response Successfully received the 1043702 byte file
[SENDER][INFO][2022-04-01 18:23:48,236] - Generator task done!
[SENDER][INFO][2022-04-01 18:23:48,237] - W0 done!
[SENDER][INFO][2022-04-01 18:23:48,237] - W1 done!
[SENDER][INFO][2022-04-01 18:23:48,237] - W2 done!
[SENDER][INFO][2022-04-01 18:23:48,237] - W3 done!
[SENDER][INFO][2022-04-01 18:23:48,237] - W4 done!
[SENDER][INFO][2022-04-01 18:23:48,237] - W5 done!
[SENDER][INFO][2022-04-01 18:23:48,237] - W6 done!
[SENDER][INFO][2022-04-01 18:23:48,237] - W7 done!
[SENDER][INFO][2022-04-01 18:23:48,237] - W8 done!
[SENDER][INFO][2022-04-01 18:23:48,238] - W9 done!
[SENDER][INFO][2022-04-01 18:23:48,238] - Done!
```

I implemented some extra stuff that I thought was a cool demo of the chosen
libraries as well, such as optionally logging to files and integrity
verification using SHA256 hashes. If you'd like to check out the extra options,
it's easy to run the server and sender separately and communicate! Here's an
example of sending only 15 files, optionally corrupting the binary file payload
after checksum computation. First start the server (just use ctrl+c to stop it
when you are done):

```shell
(takehome-env) ...$ python3 server.py
======== Running on http://127.0.0.1:8000 ========
(Press CTRL+C to quit)
```

Then in another terminal, activate the virtualenv and start the sender with
additional args and see the new options in action:

```shell
# In a new shell
...$ source takehome-env/bin/activate
(takehome-env) ...$ python3 sender.py --inject-bad-checksums -n 15
[SENDER][INFO][2022-04-01 19:35:46,704] - Generated new blob of length 849213
[SENDER][INFO][2022-04-01 19:35:46,706] - W0 wrote binary file to /tmp/sender-90a29a8b-5f65-4273-be64-b2770fe9bd58.bin
[SENDER][INFO][2022-04-01 19:35:46,714] - W0 successfully sent blob and received response Successfully received the 849213 byte file
[SENDER][INFO][2022-04-01 19:35:46,956] - Generated new blob of length 430658
...
[SENDER][INFO][2022-04-01 19:35:47,745] - Generated new blob of length 196834
[SENDER][INFO][2022-04-01 19:35:47,746] - W4 intentionally corrupting blob
[SENDER][INFO][2022-04-01 19:35:47,746] - W4 wrote binary file to /tmp/sender-d741ed52-7ce7-4a50-a31e-e7a9462ac6d8.bin
[SENDER][INFO][2022-04-01 19:35:47,749] - W4 encountered status 400 sending blob
[SENDER][INFO][2022-04-01 19:35:47,776] - Generated new blob of length 422671
[SENDER][INFO][2022-04-01 19:35:47,781] - W5 wrote binary file to /tmp/sender-9855f0b2-cfab-48b6-a795-633cf0431bf3.bin
[SENDER][INFO][2022-04-01 19:35:47,795] - W5 successfully sent blob and received response Successfully received the 422671 byte file
...
[SENDER][INFO][2022-04-01 19:35:53,747] - Generator task done!
[SENDER][INFO][2022-04-01 19:35:53,747] - W0 done!
[SENDER][INFO][2022-04-01 19:35:53,748] - W1 done!
[SENDER][INFO][2022-04-01 19:35:53,748] - W2 done!
[SENDER][INFO][2022-04-01 19:35:53,749] - W3 done!
[SENDER][INFO][2022-04-01 19:35:53,749] - W4 done!
[SENDER][INFO][2022-04-01 19:35:53,749] - W5 done!
[SENDER][INFO][2022-04-01 19:35:53,749] - W6 done!
[SENDER][INFO][2022-04-01 19:35:53,750] - W7 done!
[SENDER][INFO][2022-04-01 19:35:53,750] - W8 done!
[SENDER][INFO][2022-04-01 19:35:53,750] - W9 done!
[SENDER][INFO][2022-04-01 19:35:53,750] - Done!
```

You'll see the server noticed the shenanigans:

```shell
[SERVER][INFO][2022-04-01 19:35:46,713] - Wrote a 849213 byte file to /tmp/server-90a29a8b-5f65-4273-be64-b2770fe9bd58.bin
...
[SERVER][ERROR][2022-04-01 19:35:47,748] - Strict hash checking enabled, but hashes dont match!
[SERVER][INFO][2022-04-01 19:35:47,749] - Saving file will be skipped due to hash mismatch!
...
[SERVER][INFO][2022-04-01 19:35:52,779] - Wrote a 140303 byte file to /tmp/server-09e15d2f-c1cd-4ae6-a7f3-419ac6326e72.bin
```

## Cleanup
Once you are done experimenting with the project, you will want to remove all
the randomly generated bin files from `/tmp` (or another location if you
specified a different `-d`):

```shell
(takehome-env) ...$ rm /tmp/*.bin
```

You'll also want to deactivate and delete the virtual environment, which will
clean up the dependencies installed earlier:

```shell
(takehome-env) ...$ deactivate
...$ rm -r takehome-env/
```

# Assignment
## Verbatim Task
1.  Set up two local Python servers.
2.  On one of the servers, over the course of 10 minutes, generate 100 binary
    files of random sizes ranging from 1kb to 1Mb at random time intervals
    ranging from 1ms to 1s, encoded int16.
3.  Transfer those binary files as they are being generated from the first
    server to the second server over HTTP using Python's async io functionality,
    thereby effectively implementing data streaming from one server to the
    other.
4.  Provide a GH repo of your code.

## Interpretation
I found that some interpretation of the task was necessary, I apologize if I
misunderstood the requirements, but I think this project largely does what was
asked.

Below are some deviations/interpretations and the justifications:
* __duration requirement in (2)__ - the assignment says to create 100 files over
  the course of 10 minutes, but the maximum time between subsequent files is
  listed as 1s. Even using the maximum duration of 1s for every one of the 100
  files, that means the applications will run for a maximum of 100s (plus the
  remaining transfer time of the last few in flight files). This is far less
  than the specified runtime of 10m (600s). I took this to mean that the maximum
  runtime should be 10m, which will always be satisfied, so I ignored the 10m
  part of the assignment.
* __two servers requirement in (1)__ - the assigment specifies creating two
  servers, but then specifies that HTTP should be used for one to "transfer"
  files to the other, which implies that one is only making requests as a client
  to the other. The process doing the sending isn't really serving anything,
  since no bidirectional transfers are being done. So I ignored this requirement
  and instead of creating two servers, I created two processes - one client
  process and one server process.
* __file contents__ - the assignment involves creating binary files of random
  sizes in a certain range, at random time intervals. It specifies that the
  files should be binary files and encoded int16, but it never actually
  specifies what the file contents should be. Maybe all 0's, or all 0x0042. I
  chose to generate random contents since it seemed to fit with the theme of
  randomizing the other parameters.
* __file encoding__ - the assignment specifies that the created files must be
  "encoded int16", but as far as I can tell, this requirement does nothing and
  should be ignored. The file encoding only matters if the file contents are
  being used somehow. For example, consider a binary file that is 4 bytes long
  containing the bytes `{0x41, 0x42, 0x43, 0x44}`. The 4 bytes can be read,
  written, transferred over HTTP, etc. without ever considering whether they are
  2 signed int16s, or 4 ASCII chars, or anything else. Since the assignment
  never asks to print the list of int16 numbers or anything remotely like that,
  it doesn't matter what the encoding is. There really is no encoding, since
  there is never a time when the files are used.
* __file size__ - The assignment specifies the random file sizes as in the range
  "1kb to 1Mb". Technically the lower case 'b' in 'kb' and 'Mb' indicates
  kilobits and megabits, but it is unusual to talk about files in terms of
  megabits, so I interpreted this to be kilobytes and megabytes instead.
* __files requirement__ - the assignment asks to create binary files and send
  them. Binary can be generated in one process and sent to another without ever
  being a "file", so I interpreted this requirement as saving the binary to a
  file in both the sender and server processes.
