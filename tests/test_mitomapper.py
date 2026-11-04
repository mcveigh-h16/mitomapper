import contextlib
import csv
import io
from pathlib import Path
import tempfile
import unittest

from mitomapper import main, split_fasta


class SplitFastaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "input.fasta"
        self.output = self.root / "output"

    def write_input(self, text):
        with self.source.open("w", encoding="utf-8", newline="") as target:
            target.write(text)

    def rows(self):
        with (self.output / "map").open(encoding="utf-8", newline="") as source:
            return list(csv.reader(source))

    def test_supplied_example(self):
        project = Path(__file__).resolve().parents[1]
        source = project / "testfasta2.txt"
        original_bytes = source.read_bytes()
        map_bytes = (project / "map").read_bytes()
        self.assertEqual(split_fasta(source, self.output), 3)
        self.assertEqual({p.name for p in self.output.iterdir()},
                         {"abc.fasta", "def.fasta", "ghi.fasta", "map"})
        self.assertEqual(self.rows(), [
            ["ID", "Taxon", "R1", "R2", "Assembly", "Topology"],
            *[[name, "Xiphophorus variatus", "", "", f"{name}.fasta", "circular"]
              for name in ("abc", "def", "ghi")],
        ])
        self.assertEqual(b"".join((self.output / f"{name}.fasta").read_bytes()
                                  for name in ("abc", "def", "ghi")), original_bytes)
        self.assertEqual(source.read_bytes(), original_bytes)
        self.assertEqual((project / "map").read_bytes(), map_bytes)

    def test_complete_organism_and_preserved_lines(self):
        text = '>abc [orgn=Escherichia coli strain K12, "sample"]\r\nAcg\r\nTN\r\n>def [orgn=Xiphophorus variatus]\r\nMKW'
        self.write_input(text)
        split_fasta(self.source, self.output)
        self.assertEqual(self.rows()[1],
                         ["abc", 'Escherichia coli strain K12, "sample"', "", "", "abc.fasta", "circular"])
        self.assertEqual(self.rows()[2][1], "Xiphophorus variatus")
        self.assertEqual((self.output / "abc.fasta").read_bytes(),
                         text.split(">def")[0].encode())
        self.assertEqual((self.output / "def.fasta").read_bytes(), b">def [orgn=Xiphophorus variatus]\r\nMKW")

    def test_missing_or_empty_organism_creates_no_outputs(self):
        for header in (">def", ">def [orgn=]", ">def [orgn=   ]", ">def [orgn=unfinished"):
            with self.subTest(header=header):
                self.write_input(f">abc [orgn=Xiphophorus variatus]\nAC\n{header}\nGT\n")
                with self.assertRaisesRegex(ValueError, "Missing organism name.*'def'.*line 3"):
                    split_fasta(self.source, self.output)
                self.assertFalse(self.output.exists())

    def test_all_duplicate_ids_reported(self):
        self.write_input(">abc [orgn=Example]\nA\n>def [orgn=Example]\nT\n>abc [orgn=Example]\nG\n>def [orgn=Example]\nC\n")
        with self.assertRaisesRegex(ValueError, "Duplicate sequence IDs found: abc, def"):
            split_fasta(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_case_collisions(self):
        self.write_input(">abc [orgn=Example]\nA\n>ABC [orgn=Example]\nT\n")
        with self.assertRaisesRegex(ValueError, "conflicting Windows filenames"):
            split_fasta(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_invalid_inputs_create_no_outputs(self):
        for text in ("", "\n", ">\nAC\n", ">abc [orgn=Example]\n", ">abc [orgn=Example]\n \n>def [orgn=Example]\nT\n", "AC\n>abc [orgn=Example]\nT\n"):
            with self.subTest(text=text):
                self.write_input(text)
                with self.assertRaises(ValueError):
                    split_fasta(self.source, self.output)
                self.assertFalse(self.output.exists())

    def test_invalid_windows_names(self):
        for identifier in ("../abc", "a/b", "a\\b", "a:b", "NUL", "con.txt", "COM1", "LPT¹", "abc.", "..", "a" * 250):
            with self.subTest(identifier=identifier):
                self.write_input(f">{identifier}\nAC\n")
                with self.assertRaisesRegex(ValueError, "Windows filename"):
                    split_fasta(self.source, self.output)
                self.assertFalse(self.output.exists())

    def test_existing_outputs_preserved(self):
        self.write_input(">abc [orgn=Example]\nAC\n")
        self.output.mkdir()
        for filename in ("map", "abc.fasta", "ABC.FASTA"):
            with self.subTest(filename=filename):
                existing = self.output / filename
                existing.write_text("keep")
                with self.assertRaisesRegex(ValueError, "already exist"):
                    split_fasta(self.source, self.output)
                self.assertEqual(existing.read_text(), "keep")
                self.assertEqual(list(self.output.iterdir()), [existing])
                existing.unlink()

    def test_unrelated_files_allowed(self):
        self.write_input(">abc [orgn=Example]\nAC\n")
        self.output.mkdir()
        existing = self.output / "notes.txt"
        existing.write_text("keep")
        self.assertEqual(split_fasta(self.source, self.output), 1)
        self.assertEqual(existing.read_text(), "keep")

    def test_cli_success(self):
        self.write_input(">abc [orgn=Example]\nAC\n")
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            status = main([str(self.source), str(self.output)])
        self.assertEqual(status, 0)
        self.assertIn("Wrote 1 sequences and map", stdout.getvalue())

    def test_cli_error(self):
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            status = main([str(self.source), str(self.output)])
        self.assertEqual(status, 1)
        self.assertIn("Error:", stderr.getvalue())
        self.assertFalse(self.output.exists())

    def test_cli_requires_input_and_output(self):
        for arguments in ([], [str(self.source)]):
            with self.subTest(arguments=arguments):
                with contextlib.redirect_stderr(io.StringIO()) as stderr:
                    with self.assertRaises(SystemExit) as error:
                        main(arguments)
                self.assertEqual(error.exception.code, 2)
                self.assertIn("required", stderr.getvalue())
                self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
