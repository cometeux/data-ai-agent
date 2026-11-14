"""Run with: python -m unittest discover -s tests -v"""
import unittest

from json_utils import parse_analysis_json


class AnalysisJsonTests(unittest.TestCase):
    def test_braces_inside_narrative_do_not_break_valid_json(self):
        response = '{"summary": {"overview": "The label { is literal"}, "charts": []}'
        self.assertEqual(parse_analysis_json(response)["summary"]["overview"],
                         "The label { is literal")

    def test_markdown_fences_and_arabic(self):
        self.assertEqual(parse_analysis_json('Result:\n```json\n{"summary": "بيانات"}\n```'),
                         {"summary": "بيانات"})

    def test_invalid_prefix_before_valid_object(self):
        self.assertEqual(parse_analysis_json('Note {not JSON}. {"charts": []}'),
                         {"charts": []})

    def test_escaped_quotes_and_nested_objects(self):
        response = '{"summary": {"overview": "He said \\"{ready}\\""}, "charts": [{"x": "month"}]}'
        self.assertEqual(parse_analysis_json(response)["charts"], [{"x": "month"}])

    def test_invalid_or_empty_response(self):
        for value in (None, "", "not JSON", '{"summary":', "[]"):
            with self.subTest(value=value):
                self.assertIsNone(parse_analysis_json(value))


if __name__ == "__main__":
    unittest.main()
