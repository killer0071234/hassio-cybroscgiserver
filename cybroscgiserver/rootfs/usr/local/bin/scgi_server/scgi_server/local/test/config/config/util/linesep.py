import unittest

from lib.config.config.util.linesep import \
    detect_line_separator


class LinesepTestCase(unittest.TestCase):
    def test_detect_line_separator(self):
        line1 = "some\r\ntext\r\nwith lines"
        line2 = "some\rtext\rwith lines"
        line3 = "some\ntext\nwith lines"

        self.assertEqual(detect_line_separator(line1), "\r\n")
        self.assertEqual(detect_line_separator(line2), "\r")
        self.assertEqual(detect_line_separator(line3), "\n")


if __name__ == "__main__":
    unittest.main()
