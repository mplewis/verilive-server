import sys

from flask import Flask, jsonify

import config


app = Flask(__name__)
app.config.from_object(config.Flask)


@app.route('/')
def about():
    version = '.'.join([str(x) for x in config.Metadata.VERSION])
    return jsonify(name=config.Metadata.NAME,
                   version=version,
                   contact=config.Metadata.CONTACT)


@app.route('/compile', methods=['POST'])
def compile():
    pass


def main():
    if sys.version_info[0] != 3:
        print("This is a Python 3 script. You are running Python %s.%s.%s." %
              sys.version_info[:3])
        sys.exit(1)
    app.run()


if __name__ == '__main__':
    main()
