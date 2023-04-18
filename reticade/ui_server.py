from flask import Flask, redirect, url_for, request
from pybars import Compiler
from multiprocessing import Pipe
import time

def create_flask_app(harness_pipe, imaging_pipe, shared_dict):
    with open('reticade/static/index.html', 'r') as f:
        html_template = f.read()
    compiler = Compiler()
    template = compiler.compile(html_template)

    templated_variables = shared_dict

    app = Flask(__name__)

    @app.route('/')
    def index():
        html = template(templated_variables)
        return html


    @app.route('/init_labview', methods=["POST"])
    def init_labview():
        labview_ip_addr = request.form['ip_addr']
        print(f"connecting to {labview_ip_addr}")
        instruction = "Foo"
        harness_pipe.send(instruction)
        done = harness_pipe.recv()
        return redirect(url_for('index'))


    @app.route('/init_prairieview')
    def init_prairieview():
        print("init pview")
        templated_variables['prairieview_connected'] = True
        return redirect(url_for('index'))


    @app.route('/load_decoder', methods=["POST"])
    def load_decoder():
        print("loading decoder")
        decoder_name = request.form['decoderfile']
        templated_variables['decoder'] = decoder_name
        return redirect(url_for('index'))


    @app.route('/test_labview')
    def test_labview():
        print("test labview")
        return redirect(url_for('index'))


    @app.route('/test_prairieview')
    def test_prairieview():
        print("test pview")
        return redirect(url_for('index'))


    @app.route('/run_bmi', methods=["POST"])
    def run_bmi():
        duration = request.form['duration']
        print(f"Request to run BMI for {duration} s")
        return redirect(url_for('index'))
    
    return app
