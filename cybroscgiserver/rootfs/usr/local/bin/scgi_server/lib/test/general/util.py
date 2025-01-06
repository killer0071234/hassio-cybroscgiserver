import unittest
import datetime

from general.util import tabulate, rows_left_justified_str


class UtilsTest(unittest.TestCase):
    def test_tabulate(self):
        column_width = [18, 10, 20, 15, 20, 15, 20, 20, 35]
        headers = [
            "push",
            "nad",
            "ip address",
            "status",
            "program",
            "alc file",
            "downloaded",
            "response",
            "last update"
        ]
        tabular_data = [
            '17-09-24 17:51:33',
            10060,
            '192.168.1.47:8442',
            None,
            None,
            False,
            'N/A',
            None,
            datetime.datetime(
                2024,
                9,
                17,
                17,
                51,
                33,
                327672
            )
        ]
        td = [list(map(str, tabular_data))]
        print(td)
        r = tabulate(column_width, headers, td)
        print('====')
        print(r)
        print('===')
        self.maxDiff = None
        self.assertEqual(
            first=r,
            second="\n       push       |   nad    |     ip address     |     "
                   "status    |      program       |    alc file   |     downl"
                   "oaded     |      response      |            last update   "
                   "         \n-----------------------------------------------"
                   "----------------------------------------------------------"
                   "----------------------------------------------------------"
                   "----------\n17-09-24 17:51:33 |10060     |192.168.1.47:844"
                   "2   |None           |None                |False          |"
                   "N/A                 |None                |2024-09-17 17:51"
                   ":33.327672         \n"
        )

    def test_rows_left_justified_str(self):
        column_widths = [18, 10, 20, 15, 20, 15, 20, 20, 35]
        row = [
            '17-09-24 17:51:33',
            '10060',
            '192.168.1.47:8442',
            'None',
            'None',
            'False',
            'N/A',
            'None',
            '2024-09-17 17:51:33.327672'
        ]

        row_str = rows_left_justified_str(row, column_widths)

        self.assertEqual(row_str, "")


if __name__ == '__main__':
    unittest.main()
