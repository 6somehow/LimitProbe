import json
import unittest

from paperprobe.multimodal_decomposition import make_content, parse_response
from paperprobe.paper_decomposition import inventory


class MultimodalDecompositionTest(unittest.TestCase):
    def test_added_images_preserve_the_exact_legacy_text_input(self):
        data = {"pages": [{"page": 1, "text": "TeSA 属性"}]}
        images = [{"page": 1, "data_url": "data:image/jpeg;base64,AA=="},
                  {"page": 2, "data_url": "data:image/jpeg;base64,BB=="}]
        content = make_content(data, images)
        self.assertEqual(make_content(data, []), json.dumps(data, ensure_ascii=False))
        self.assertEqual(content[0]["text"], make_content(data, []))
        self.assertEqual([p["image_url"]["url"] for p in content[1:]],
                         [image["data_url"] for image in images])

    def test_incomplete_generation_is_not_accepted_as_a_complete_map(self):
        response = {"choices": [{"finish_reason": "length", "message": {"content": '{"mechanisms":[]}'}}]}
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            parse_response(response)

    def test_fenced_json_is_decoded_without_changing_its_fields(self):
        content = chr(96) * 3 + 'json\n{"mechanisms":[]}\n' + chr(96) * 3
        result = parse_response({"choices": [{"finish_reason": "stop", "message": {"content": content}}]})
        self.assertEqual(result, {"mechanisms": []})

    def test_replay_cap_does_not_change_the_legacy_default(self):
        mechanisms = [dict(name=f"M{i}", description="Initialize graph", pages=[1],
                           depends_on=[], evidence=[dict(page=1, quote="Initialize every graph node.")])
                      for i in range(19)]
        raw = dict(mechanisms=mechanisms, claims=[], coverage=[
            dict(page=1, role="technical", topics=[], note="Algorithm")])
        with self.assertRaises(ValueError):
            inventory(raw, ["Initialize every graph node."])
        self.assertEqual(len(inventory(raw, ["Initialize every graph node."], max_mechanisms=60)["mechanisms"]), 19)
