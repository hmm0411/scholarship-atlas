import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from check_sources import clean_html, excerpt, load_json

class MonitorTests(unittest.TestCase):
    def test_strip_html(self):
        self.assertEqual(clean_html('<nav>menu</nav><main>Deadline &amp; date</main><script>secret()</script>'), 'Deadline & date')
    def test_excerpt(self):
        self.assertGreaterEqual(len(excerpt('Apply before deadline January 2027 for scholarship students')), 1)
    def test_sources(self):
        sources=load_json(Path(__file__).resolve().parents[1]/'data'/'sources.json',{})['sources']
        self.assertGreaterEqual(len(sources),20)
        self.assertEqual(len({s['id'] for s in sources}),len(sources))
        self.assertTrue(all(s['url'].startswith('https://') for s in sources))
if __name__=='__main__':unittest.main()
