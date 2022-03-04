from lib.ColorPrint import color_print, print_error, print_warning, print_success


def test_print_warning():
    print_warning("lmao", "eyyy")


def test_print_error():
    print_error("lmao. This should be white", "eyyy this should be white on red")


def test_print_success():
    print_success("Success! This should be green")

