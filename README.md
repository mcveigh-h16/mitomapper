# FASTA splitter

Split a multi-sequence FASTA file into one `.fasta` file per sequence and generate a mapping CSV named `map`. Uses only the Python standard library; no packages need installing. Python 3.10 or newer is required.

## Download the project from GitHub

1. Install Python 3.10 or newer if it is not already available. Windows users can download it from [python.org](https://www.python.org/downloads/); Linux users can use their distribution's package manager. On Linux, also install your distribution's Python `venv` support if it is packaged separately.
2. Choose one of the download methods below. You do not need a GitHub account to download this public project.
3. Open PowerShell on Windows or a terminal on Linux, enter the downloaded project directory, and follow the setup instructions for your operating system.

### Option A: Clone using Git

Install [Git](https://git-scm.com/downloads) if needed. A clone is a local copy of the GitHub repository. In your terminal, move to the folder where you want to keep the project, then run:

```sh
git clone https://github.com/mcveigh-h16/mitomapper.git
cd mitomapper
```

### Option B: Download a ZIP without Git

1. Open [mcveigh-h16/mitomapper on GitHub](https://github.com/mcveigh-h16/mitomapper).
2. Select **Code**, then **Download ZIP**.
3. Extract the ZIP archive. Open a terminal in the extracted `mitomapper-main` folder, or use `cd` followed by its path. For example, if you extracted it into your current directory:

```sh
cd mitomapper-main
```

Run the setup commands below from the folder containing `mitomapper.py` and `README.md`. Do not run them inside the ZIP archive. No `pip install` command is needed: this project runs directly as a Python script and has no third-party dependencies.

## Setup on Windows (PowerShell)

For a new download, create your own virtual environment. A virtual environment is a project-specific Python environment. The repository includes a Windows Python 3.13.1 snapshot, but its paths refer to the original machine. The `--clear` option replaces the downloaded `.venv` contents with an environment for your computer; use it only for initial setup, as it removes any packages already installed in that environment.

```powershell
py -3 -m venv --clear .venv
.\.venv\Scripts\Activate.ps1
python mitomapper.py fasta.orig output
```

The last command runs the included example. You should see a message confirming that three sequences and a mapping file were written to the `output` folder.

In future terminal sessions, activate the existing environment before running the script:

```powershell
.\.venv\Scripts\Activate.ps1
```

Activation is optional. If PowerShell blocks the activation script, invoke the environment's interpreter directly:

```powershell
.\.venv\Scripts\python.exe mitomapper.py fasta.orig output
```

## Setup on Linux

The included Windows environment cannot run on Linux. From the project directory, create a local virtual environment using Python 3.10 or newer. For initial setup, `--clear` replaces the downloaded `.venv` contents; omit this step in future terminal sessions to keep your existing environment.

```sh
python3 -m venv --clear .venv
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

## Run with your own FASTA file

Replace `fasta.orig` with your input filename and `output` with the directory you want to create:

```sh
python mitomapper.py my_sequences.fasta my_results
```

You can copy your input file into the project folder or provide its full path. Put quotes around paths containing spaces. Open `my_results` to find the individual FASTA files and the CSV file named `map`; a text editor or spreadsheet program can open the CSV. To run the example again, choose a new output directory, such as `output_example2`, because existing output files are never overwritten.

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
