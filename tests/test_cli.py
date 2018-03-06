import io

from mock import patch
from unittest import TestCase

from cloudcrane.cli import cli


class TestCLI(TestCase):

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_should_return_help_page(self, out):
        with self.assertRaises(SystemExit) as ex:
            cli(['--help'])
        output = out.getvalue()

        self.assertEqual(ex.exception.code, 0)
        self.assertIn('Cloudcrane', output)
        self.assertIn('Usage:', output)
        self.assertIn('Options:', output)
        self.assertIn('Commands:', output)
