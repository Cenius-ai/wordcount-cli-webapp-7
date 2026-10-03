# Installing wordcount

The tool is one standard-library Python file; "installing" it is optional. This
document lists everything needed to run it from a clean checkout.

## Prerequisites (not installed by any script)

| Requirement | Why | Check |
| --- | --- | --- |
| Python 3.8 or newer | runs `wordcount.py` | `python3 --version` |
| bash | runs `install.sh` and `demo.sh` | `bash --version` |

Nothing else: no compiler, no database, no service, no environment variables,
no network access at runtime. `install.sh` never calls `sudo`, `apt-get`,
`pkg`, `brew` or any other system package manager — it only uses `pip`.

## Package manager

`pip` — the single package manager for this project, matching
`requirements.txt`.

## Steps

### 1. Install dependencies and the optional console script

```bash
bash install.sh
```

This one script does everything, in order, and then **exits** (it never starts
a long-running process):

1. upgrades `pip`, `setuptools` and `wheel`;
2. `pip install -r requirements.txt` — the test runner, the only declared
   dependency;
3. `pip install --no-build-isolation -e .` — the optional `wordcount` console
   script (the program itself has no dependencies);
4. runs a self-check that imports the module, prints `count_words("the quick
   brown fox") -> 4` and counts `examples/sample.txt`.

It is idempotent: run it as often as you like.

Equivalent manual commands:

```bash
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -r requirements.txt
python3 -m pip install --no-build-isolation -e .
```

### 2. Seed data

There is **no seed step**. The tool owns no database, no cache and no stored
state — it only ever reads the file you name. The sample inputs the demo and
the tests use are committed in `examples/`:

| File | Purpose |
| --- | --- |
| `examples/sample.txt` | the canonical four-word file |
| `examples/release_notes.md` | 216 words of real prose, used in the demo |
| `examples/empty.txt` | zero-byte file → prints `0` |
| `examples/whitespace.txt` | only spaces and tabs → prints `0` |
| `examples/not_utf8.txt` | Latin-1 bytes → reported as not valid UTF-8 |

### 3. Verify the install

```bash
python3 wordcount.py examples/sample.txt     # prints 4, exit status 0
python3 wordcount.py missing.txt             # prints an error on stderr, exit 1
python3 wordcount.py                         # prints the usage line, exit 2
```

### 4. Run it

```bash
python3 wordcount.py <path>                  # the whole interface
bash demo.sh                                 # non-interactive walkthrough
```

### 5. Run the tests

```bash
python3 -m pytest
```

## Uninstalling

```bash
python3 -m pip uninstall wordcount-cli        # only if you ran install.sh
```

Nothing else was added to your machine.
