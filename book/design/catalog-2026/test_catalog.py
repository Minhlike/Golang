"""Tests of prototype invariants. No mutations outside the prototype directory."""
import json
import unittest

from build_catalog import HERE, ROOT, parse, sha, protected_snapshot, ARRAY_LABELS, Code, fonts, WIDTH


class PrototypeTests(unittest.TestCase):
    def test_all_markdown_roundtrips_bytes(self):
        files=list((ROOT/"book/chapters").glob("*.md"))+list((ROOT/"book/appendices").glob("*.md"))
        self.assertEqual(len(files),33)
        for path in files:
            self.assertEqual("".join(n["raw"] for n in parse(path)).encode("utf-8"),path.read_bytes())

    def test_all_protected_files_unchanged(self):
        self.assertEqual(protected_snapshot(),json.loads((HERE/"protected_snapshot.json").read_text(encoding="utf-8")))

    def test_tab_expansion_is_not_byte_preservation(self):
        raw=(HERE/"copy_fixture.txt").read_bytes()
        self.assertIn(b"\t",raw)
        self.assertNotEqual(raw,raw.decode("utf-8").expandtabs(4).encode("utf-8"))
        self.assertIn(b"  \n",raw)
        self.assertIn(b"\n\n",raw)
        self.assertNotEqual(raw,raw.replace(b"\n",b"\r\n"))

    def test_fixture_matches_recorded_hash(self):
        results=json.loads((HERE/"copy_code_results.json").read_text(encoding="utf-8"))
        self.assertEqual(sha((HERE/"copy_fixture.txt").read_bytes()),results["fixture_sha256"])

    def test_tab_code_payload_kept_raw(self):
        nodes=parse(ROOT/"book/chapters/01-doc-va-viet-mot-chuong-trinh-go.md")
        block=next(n for n in nodes if n["type"]=="code" and "x, y := 2, 3" in n["payload"])
        self.assertIn("\tx := 4",block["payload"])
        self.assertEqual(block["payload"],Code(block["payload"]).payload)

    def test_vector_semantics_match_source(self):
        source=(ROOT/"assets/diagrams/array-copy.puml").read_text(encoding="utf-8")
        self.assertTrue(all(label in source for label in ARRAY_LABELS))
        self.assertIn("a ..> b",source)

    def test_code_overflow_rejected_not_shrunk(self):
        fonts()
        with self.assertRaises(ValueError):Code("x"*100).wrap(WIDTH,700)

    def test_visual_ledger_is_sha_bound_and_complete(self):
        ledger=json.loads((HERE/"visual_review.json").read_text(encoding="utf-8"))
        self.assertEqual(ledger["pdf_sha256"],sha((HERE/"catalog.pdf").read_bytes()))
        self.assertEqual([p["page"] for p in ledger["pages"]],list(range(1,24)))
        self.assertTrue(all(p["observation"] and p["status"]=="VISUAL_PASS" for p in ledger["pages"]))


if __name__=="__main__":unittest.main()
