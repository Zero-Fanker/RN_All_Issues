import sys

def get_value_from_args(short_arg: str,
                        long_arg: str) -> str|None:
    argv = sys.argv
    result = None
    if (long_arg in argv):
        result = argv[argv.index(long_arg) + 1]
    if (short_arg in argv):
        result = argv[argv.index(short_arg) + 1]
    return result
