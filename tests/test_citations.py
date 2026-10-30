"""devkit/citations.py: stock-client addresses and symbols are refused in what we write; ordinary hex is not."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "devkit"))
import citations  # noqa: E402


class CitationTests(unittest.TestCase):
    def test_citations_are_found(self):
        for text in ("// test (`CanTargetUnit 0x6e4440`).", "/// The last-input stamp `[0xcf0bc8]` drives it",
                     "/// `CGGameUI::SetUIScale` scales the frame", "// as the reference's callback clamps",
                     "/// AddOn_GetTitle 0x51df20 sorts them", "// sub_51DF20 does this", "keeps [0x00bd0778] alive",
                     "/// The reference client never shows it", "-- CGUnit_C::GetAura reads it"):
            self.assertTrue(citations.hits_in_text(text), text)

    def test_ordinary_code_is_not_a_citation(self):
        for text in ("color = 0xffcc00", "return 0x123456;", "let seed = 0x00100001;", "Color 0xff00ff",
                     "std::vector<int> v;", "ChatHandler::SendSysMessage", "see the reference docs",
                     "0x7FED7FED", "hash & 0xFFFFFFFF"):
            self.assertFalse(citations.hits_in_text(text), text)

    def test_in_a_patch_only_added_lines_count(self):
        patch = ("--- a/x.rs\n+++ b/x.rs\n@@ -1,2 +1,2 @@\n /// upstream `CanTargetUnit 0x6e4440`\n"
                 "-/// old `[0xcf0bc8]`\n+/// the stock targeting check\n")
        self.assertEqual(citations.hits("x.patch", patch), [])
        self.assertTrue(citations.hits("x.patch", patch + "+// test (`CanTargetUnit 0x6e4440`).\n"))

    def test_the_client_patches_cite_nothing_on_their_own_lines(self):
        pdir = os.path.join(ROOT, "labs", "openvanilla-realm", "realm", "patches")
        for name in sorted(os.listdir(pdir)):
            if name.endswith(".patch"):
                with open(os.path.join(pdir, name), encoding="utf-8") as f:
                    self.assertEqual(citations.hits(name, f.read()), [], name)


if __name__ == "__main__":
    unittest.main()
