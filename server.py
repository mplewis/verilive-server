import config

import ivernetp

from flask import Flask, jsonify, request

import sys
import tempfile
import shutil
import subprocess
import time
from os import path
from multiprocessing import Process, Queue


app = Flask(__name__)
app.config.from_object(config.Flask)


class CompileTimeoutError(Exception):
    pass


def compile_task(paths, result_queue):
    cmd = ['iverilog', '-N', paths['netlist'], '-o', paths['compiled'],
           paths['module'], paths['testbench']]
    try:
        subprocess.check_call(cmd, cwd=paths['temp_dir'])
        stdout = (subprocess.check_output(['vvp', paths['compiled']],
                                          cwd=paths['temp_dir'])
                  .decode('utf-8'))
    except subprocess.CalledProcessError as e:
        result_queue.put((str(e), None))
    else:
        result_queue.put((None, stdout))


def compile_with_timeout(paths, timeout_secs):
    result_queue = Queue()
    args = (paths, result_queue)
    compile_process = Process(target=compile_task, args=args)
    compile_process.start()
    compile_process.join(timeout_secs)

    if compile_process.is_alive():
        compile_process.terminate()
        raise CompileTimeoutError

    error, stdout = result_queue.get()
    return stdout


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

    try:
        paths = {
            'temp_dir': temp_dir,
            'module': path.join(temp_dir, 'module.v'),
            'testbench': path.join(temp_dir, 'testbench.v'),
            'netlist': path.join(temp_dir, 'netlist'),
            'compiled': path.join(temp_dir, 'compiled.vvp'),
            'waveform': path.join(temp_dir, 'waveform.vcd')
        }

        with open(paths['module'], 'w') as f:
            f.write(request.json['module'])
        with open(paths['testbench'], 'w') as f:
            f.write(request.json['testbench'])

        start_time = time.time()
        timeout_secs = config.Compiler.COMPILE_TIMEOUT
        try:
            stdout = compile_with_timeout(paths, timeout_secs)
        except CompileTimeoutError:
            err = {'error': 'Compile process took too long; '
                            'max time is %s seconds' % timeout_secs}
            return jsonify(err), 409
        end_time = time.time()

        with open(paths['netlist']) as f:
            raw_netlist = f.read()

        netlist = ivernetp.process_netlist.netlist_to_json(raw_netlist)

        try:
            with open(paths['waveform']) as f:
                waveform = f.read()
        except OSError:
            waveform = None

        return jsonify(stdout=stdout, waveform=waveform, netlist=netlist,
                       seconds=end_time - start_time)

    finally:
        shutil.rmtree(temp_dir)


def main():
    if sys.version_info[0] != 3:
        print("This is a Python 3 script. You are running Python %s.%s.%s." %
              sys.version_info[:3])
        sys.exit(1)
    app.run()


if __name__ == '__main__':
    main()
