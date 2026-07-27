from paginate import page_slice


def test_first_page():
    assert page_slice(list(range(10)), 1, 3) == [0, 1, 2]


def test_second_page():
    assert page_slice(list(range(10)), 2, 3) == [3, 4, 5]


def test_last_partial_page():
    assert page_slice(list(range(10)), 4, 3) == [9]
