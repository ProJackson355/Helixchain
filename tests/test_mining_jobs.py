import unittest

import node.node as node_api


class ExternalOnlyMiningTests(unittest.TestCase):
    def test_node_exposes_templates_and_submissions_but_no_local_mining(self):
        paths = {route.path for route in node_api.app.routes}
        self.assertIn("/mining/work", paths)
        self.assertIn("/mining/submit", paths)
        self.assertNotIn("/mine", paths)
        self.assertNotIn("/mine/start", paths)
        self.assertNotIn("/mine/status/{job_id}", paths)


if __name__ == "__main__":
    unittest.main()
