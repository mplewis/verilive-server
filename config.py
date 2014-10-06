from os.path import join, abspath


class Flask:
    DEBUG = False
    HOST = '0.0.0.0'


class Compiler:
    COMPILE_TIMEOUT = 0.5  # seconds
    BINARY_DIR = abspath('iverilog/bin')
    IVERILOG_PATH = join(BINARY_DIR, 'iverilog')
    VVP_PATH = join(BINARY_DIR, 'vvp')


class Metadata:
    NAME = 'Verilive Server'
    VERSION = (0, 0, 1)
    CONTACT = 'info@verilog.me'


class Misc:
    TEMP_DIR_PREFIX = 'verilive_'
