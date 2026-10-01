import unittest
from validate_manuscript_diagrams import character_diagrams


class CharacterDiagramContract(unittest.TestCase):
    def test_reported_credential_diagram_is_rejected(self):
        self.assertEqual(character_diagrams(
            "heading\n~~~\n[LoadDefaultConfig]\n   │\n   ▼\n[Credentials]\n~~~\n"), [2])

    def test_ascii_sequence_is_rejected_even_when_labelled_text(self):
        self.assertEqual(character_diagrams(
            "```text\n[GitHub] --> [Webhook server]\n```\n"), [1])

    def test_real_code_and_exact_output_are_preserved(self):
        for text in (
            '~~~go\nfmt.Println("[A] --> [B]")\n~~~\n',
            '~~~\n=== RUN   TestExample\n--- PASS: TestExample (0.00s)\nPASS\n~~~\n',
            '```text\nOperation cannot be fulfilled on pods\n```\n',
            '~~~text\nflow: {heap} ← &{storage for append(...)}:\n~~~\n',
        ):
            with self.subTest(text=text):
                self.assertEqual(character_diagrams(text), [])

    def test_directory_tree_is_preserved(self):
        self.assertEqual(character_diagrams(
            "~~~\nprojects/opsprobe/\n├── cmd/\n│   └── main.go\n└── go.mod\n~~~\n"), [])

    def test_fence_inside_code_does_not_end_block(self):
        self.assertEqual(character_diagrams(
            '~~~go\n// ``` is a different delimiter\nfmt.Println("[A] --> [B]")\n~~~\n'), [])


if __name__ == "__main__":
    unittest.main()
