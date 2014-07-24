import sys
import tempfile
import shutil
import subprocess
from os import path

from flask import Flask, jsonify, request

import config


app = Flask(__name__)
app.config.from_object(config.Flask)


@app.after_request
def allow_cors(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    return response


@app.route('/')
def about():
    version = '.'.join([str(x) for x in config.Metadata.VERSION])
    return jsonify(name=config.Metadata.NAME,
                   version=version,
                   contact=config.Metadata.CONTACT)


@app.route('/compile', methods=['POST'])
def compile():
    for arg in ('module', 'testbench'):
        if arg not in request.json:
            return 'Argument %s not found in posted JSON' % arg, 400

    temp_dir = tempfile.mkdtemp(prefix=config.Misc.TEMP_DIR_PREFIX)
    module_path = path.join(temp_dir, 'module.v')
    testbench_path = path.join(temp_dir, 'testbench.v')
    compiled_path = path.join(temp_dir, 'compiled.vvp')
    waveform_path = path.join(temp_dir, 'waveform.vcd')

    with open(module_path, 'w') as f:
        f.write(request.json['module'])
    with open(testbench_path, 'w') as f:
        f.write(request.json['testbench'])

    subprocess.call(['iverilog', '-o', compiled_path, module_path,
                     testbench_path], cwd=temp_dir)
    stdout = (subprocess.check_output(['vvp', compiled_path], cwd=temp_dir)
              .decode('utf-8'))

    with open(waveform_path) as f:
        waveform = f.read()
    shutil.rmtree(temp_dir)
    return jsonify(stdout=stdout, waveform=waveform)


def main():
    if sys.version_info[0] != 3:
        print("This is a Python 3 script. You are running Python %s.%s.%s." %
              sys.version_info[:3])
        sys.exit(1)
    app.run()


if __name__ == '__main__':
    main()
