# FASTA splitter

Split a multi-sequence FASTA file into one `.fasta` file per sequence and generate a mapping CSV named `map`. Uses only the Python standard library; no packages need installing. Python 3.10 or newer is required.

## Setup on Windows (PowerShell)

The project includes a snapshot of its Windows Python 3.13.1 virtual environment in `.venv`. Virtual environments contain machine-specific paths; recreate it using the setup command below when using a different machine. On the original machine, reuse it:

```powershell
.\.venv\Scripts\Activate.ps1
python mitomapper.py fasta.orig output
```

For a fresh checkout, first create the environment:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Activation is optional. You can invoke the environment's interpreter directly:

```powershell
.\.venv\Scripts\python.exe mitomapper.py fasta.orig output
```

## Setup on Linux

The included Windows environment cannot run on Linux. From the project directory, create a local virtual environment using Python 3.10 or newer:

```sh
python3 -m venv .venv
```

Activate it using the command for your shell. For Bash or Zsh:

```sh
source .venv/bin/activate
```

For C shell (`csh` or `tcsh`):

```csh
source .venv/bin/activate.csh
```

After activation, run the script:

```sh
python mitomapper.py fasta.orig output
```

Use `deactivate` to leave the environment. Activation is optional; you can also run the script directly:

```sh
.venv/bin/python mitomapper.py fasta.orig output
```

## Usage and outputs

```text
python mitomapper.py INPUT_FASTA OUTPUT_DIRECTORY
```

Both arguments are required: specify the input filename first and the output directory second. Relative paths are resolved from the current working directory. Quote paths containing spaces. Missing output directories are created. For `python mitomapper.py fasta.orig output`, the script creates:

```text
output/
    abc.fasta
    def.fasta
    ghi.fasta
    map
```

Each FASTA file retains its complete original header, sequence letter case, and line wrapping. The first whitespace-delimited token after `>` supplies the filename. Thus `>abc [orgn=Escherichia coli]` produces `abc.fasta`.

The `map` file contains CSV rows in input order:

```csv
ID,Taxon,R1,R2,Assembly
abc,Escherichia coli,,,abc.fasta
def,,,,def.fasta
ghi,,,,ghi.fasta
```

`Taxon` contains the complete text after `orgn=` through the closing `]`, excluding the prefix and brackets. For example, `[orgn=Escherichia coli strain K12]` becomes `Escherichia coli strain K12`. The first matching `[orgn=...]` annotation is used. Missing annotations produce a blank Taxon. CSV quoting preserves commas and quotes in organism names. R1 and R2 are blank; Assembly is the FASTA filename relative to the output directory.

## Errors

The script validates input and output names before writing files. It reports all duplicate sequence IDs and exits with status 1. IDs differing only by case also cause an error because their Windows filenames conflict. Unsafe Windows filenames, empty input, missing IDs, empty sequences, and sequence content before the first header are rejected. Blank lines are allowed; sequence letters are not restricted to a DNA alphabet.

Existing output files are never overwritten. Use a fresh destination or move existing outputs before rerunning. An existing directory containing unrelated files is allowed. Input and the example `map` are preserved. Success prints the sequence count and destination; errors are printed to standard error.

Records are held in memory during validation, so available memory must accommodate the input file.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
