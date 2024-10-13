from datetime import timedelta


def tabulate(column_widths: list[int],
             headers_list: list[str],
             tabular_data: list[list[str]]) -> str:
    rows_list = []
    header = centered_header_str(headers_list, column_widths)
    rows_list.append(header)
    row_len = 0

    for width in column_widths:
        row_len += width

    rows_list.append('-' * row_len)
    for row in tabular_data:
        row_str = rows_left_justified_str(row, column_widths)
        rows_list.append(row_str)

    return '\n' + '\n'.join(rows_list) + '\n'


def centered_header_str(headers: list[str], column_widths: list[int]) -> str:
    titles_centered = []
    for i, value in enumerate(headers):
        column_width = column_widths[i]
        title_centered = value.center(column_width)
        titles_centered.append(title_centered)

    return '|'.join(titles_centered)


def rows_left_justified_str(row_data: list[str],
                            column_widths: list[int]) -> str:
    row_data_left_justified = []
    for i, value in enumerate(row_data):
        column_width = column_widths[i]
        value_left_justified = value.ljust(column_width)
        row_data_left_justified.append(value_left_justified)
    return '|'.join(row_data_left_justified)


def humanize_timedelta(td_object: timedelta) -> str:

    seconds = int(td_object)
    sec = seconds % 60
    days = int(seconds / 60 / 60 / 24)
    hours = int(seconds / 60 / 60 % 24)
    minutes = int(seconds / 60 % 60)

    return "{} days, {:02}:{:02}:{:02}".format(days, hours, minutes, sec)