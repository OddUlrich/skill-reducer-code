import unittest
from pathlib import Path
import shutil

from skillreducer.dataset import make_dataset
from skillreducer.eval import retention
from skillreducer.io import load_skills
from skillreducer.markdown import split_items
from skillreducer.reproduce import reproduce
from skillreducer.stage1 import ddmin
from skillreducer.stage2 import classify_item


class SkillReducerCoreTests(unittest.TestCase):
    def test_retention(self):
        self.assertEqual(retention(0, 0), 1.0)
        self.assertEqual(retention(0.5, 0.25), 0.5)
        self.assertEqual(retention(0.5, 0.75), 1.0)

    def test_markdown_split_and_classify(self):
        items = split_items("# A\n\n## Example\nUser: x\n\n```yaml\na: b\n```")
        labels = [classify_item(item) for item in items]
        self.assertIn("example", labels)
        self.assertIn("template", labels)

    def test_ddmin_keeps_query_terms(self):
        result = ddmin(["JWT auth", "unrelated filler", "OAuth note"], ["Need JWT auth"])
        self.assertTrue(any("JWT" in unit for unit in result))

    def test_dataset_and_reproduce(self):
        root = Path.cwd() / ".test-tmp"
        if root.exists():
            shutil.rmtree(root)
        try:
            dataset = root / "data"
            make_dataset(dataset, "small")
            skills = load_skills(dataset / "skills")
            self.assertEqual(len(skills), 12)
            out = root / "run"
            summary = reproduce(dataset, out)
            self.assertEqual(summary["reduction"]["skills"], 12)
            self.assertTrue((out / "reports" / "report.md").exists())
            self.assertTrue((out / "compressed" / "reduction.jsonl").exists())
        finally:
            if root.exists():
                shutil.rmtree(root)


if __name__ == "__main__":
    unittest.main()
