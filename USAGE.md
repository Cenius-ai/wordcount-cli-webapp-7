# Using wordcount

Every walkthrough below was run against the code in this checkout. There is
exactly one invocation form, so this is a short document.

## 1. Count the words in a file

```console
$ python3 wordcount.py examples/sample.txt
4
$ echo $?
0
```

The file is read as UTF-8 and counted; the number is the only thing on stdout.

## 2. Files that legitimately count as zero

A zero-byte file and a file holding nothing but whitespace both print `0` — a
whitespace run is never a word, and empty text split on whitespace yields
nothing.

```console
$ python3 wordcount.py examples/empty.txt
0
$ python3 wordcount.py examples/whitespace.txt
0
```

## 3. Runs of separators never inflate the count

Tabs, newlines and repeated spaces all separate words, and leading or trailing
whitespace is ignored, so the same sentence split across lines still counts the
same:

```console
$ printf 'one  two\tthree\n four ' > /tmp/odd.txt
$ python3 wordcount.py /tmp/odd.txt
4
```

## 4. Use it in a script or a pipeline

stdout carries the integer plus one newline and nothing else, so capture and
pipes behave without trimming:

```console
$ words=$(python3 wordcount.py examples/release_notes.md)
$ echo "counted $words words"
counted 216 words
$ python3 wordcount.py examples/release_notes.md | wc -c
4
```

Branch on the exit status:

```bash
if python3 wordcount.py "$1" > /tmp/count.txt; then
    echo "the file has $(cat /tmp/count.txt) words"
else
    echo "could not count $1" >&2   # the reason is already on stderr
fi
```

| Exit status | Meaning | stdout |
| --- | --- | --- |
| `0` | counted | the integer |
| `1` | the path could not be read as UTF-8 text | empty |
| `2` | the command line did not name exactly one path | empty |

## 5. What a failure looks like

Each problem is one sentence on stderr naming the path. No traceback ever
reaches the terminal.

```console
$ python3 wordcount.py missing.txt
wordcount: missing.txt: no such file
$ echo $?
1

$ python3 wordcount.py examples
wordcount: examples: is a directory

$ python3 wordcount.py examples/not_utf8.txt
wordcount: examples/not_utf8.txt: not valid UTF-8 text
```

A file that exists but cannot be read is reported the same way, with
`permission denied`, when the user genuinely lacks read permission.

## 6. A bad command line

Exactly one path is required. With none, or with more than one, the same
one-line usage message goes to stderr and the status is `2`:

```console
$ python3 wordcount.py
usage: wordcount.py <path>
$ echo $?
2

$ python3 wordcount.py a.txt b.txt
usage: wordcount.py <path>
$ echo $?
2
```

There are no options. `-h`, `--help` and `--version` are not part of the
contract; `python3 wordcount.py -h` is read as the path `-h` and reported as a
missing file.

## 7. Terminal colour

The diagnostic label and the usage label are tinted with the project accent
(`#00906f`) **only** when stderr is a terminal. Piped, redirected or recorded
output is plain text, `NO_COLOR=1` forces plain text even in a terminal, and
`TERM=dumb` does the same. The count on stdout is never coloured.

```console
$ NO_COLOR=1 python3 wordcount.py missing.txt 2>&1
wordcount: missing.txt: no such file
```

## 8. Counting something large

The whole file is read into memory (that is the documented behaviour for
enormous files) and counting is linear. A 1.4 MB file of 217,200 words — the
one `demo.sh` builds — is counted in well under a second:

```console
$ bash demo.sh
...
4 · Size and determinism — a multi-megabyte file, counted in milliseconds
   1375600 bytes → 217200 words in 161 ms, and the same integer on a second run
```

## 9. The walkthrough script

```console
$ bash demo.sh
```

runs all of the above non-interactively, prints an aligned table of results,
and exits non-zero if any expectation it checked did not hold. It is the
quickest way to see the whole contract at once.
