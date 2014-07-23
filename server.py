import sys


def main():
    if sys.version_info[0] != 3:
        print("This is a Python 3 script. You are running Python %s.%s.%s." %
              sys.version_info[:3])
        sys.exit(1)
    print('OK')


if __name__ == '__main__':
    main()
