from flask import Flask, redirect, url_for, request
from pybars import Compiler
from multiprocessing import Pipe
from reticade.interprocess_messages import ProcessMessage
import datetime
import time
import logging

logging.basicConfig(format='[%(asctime)s] [%(levelname)s] %(message)s',
                    datefmt='%H:%M:%S', level=logging.INFO)

def create_flask_app(harness_pipe, imaging_pipe, udp_rx_pipe, shared_dict):
    with open('reticade/static/index.html', 'r') as f:
        html_template = f.read()
    compiler = Compiler()
    template = compiler.compile(html_template)

    templated_variables = shared_dict

    app = Flask(__name__)

    @app.route('/')
    def index():
        shared_dict['refresh_time'] = datetime.datetime.now().strftime('%H:%M:%S')
        html = template(templated_variables)
        return html


    @app.route('/init_labview', methods=["POST"])
    def init_labview():
        labview_ip_addr = request.form['ip_addr']
        logging.info(f"UI Request: initialise labview, data: {labview_ip_addr}")
        if shared_dict['labview_connected'] == True:
            logging.warn("Labview is already connected, ignoring request")
        elif shared_dict['harness_busy'] == True:
            logging.warn("Harness is busy, ignoring request")
        else:
            instruction_1 = (ProcessMessage.SEND_CONNECT_LABVIEW, labview_ip_addr)
            udp_rx_pipe.send(instruction_1)
            done = udp_rx_pipe.recv()
            if done != ProcessMessage.ACK_CONNECT_LABVIEW:
                logging.error(f"Expected ACK_CONNECT_LABVIEW from udp server, received {done}")
            instruction_2 = (ProcessMessage.SEND_CONNECT_LABVIEW, labview_ip_addr)
            harness_pipe.send(instruction_2)
            done = harness_pipe.recv()
            if done != ProcessMessage.ACK_CONNECT_LABVIEW:
                logging.error(f"Expected ACK_CONNECT_LABVIEW from harness, received {done}")
        return redirect(url_for('index'))


    @app.route('/init_prairieview')
    def init_prairieview():
        logging.info("UI Request: initialise prairieview")
        if shared_dict['prairieview_connected'] == True:
            logging.warn("Imaging already configured, ignoring request")
        elif shared_dict['imaging_busy'] == True:
            logging.warn("Imaging process is busy,ignoring request")
        else:
            imaging_pipe.send((ProcessMessage.SEND_CONNECT_PRAIRIEVIEW, 0))
            done = imaging_pipe.recv()
            if done != ProcessMessage.ACK_CONNECT_PRAIRIEVIEW:
                logging.error(f"Expected ACK_CONNECT_PRAIRIEVIEW from imaging pipe, received: {done}")

            # Only open the harness connection once the shared memory has been set up
            harness_pipe.send((ProcessMessage.SEND_CONNECT_PRAIRIEVIEW, 0))
            done = harness_pipe.recv()
            if done != ProcessMessage.ACK_CONNECT_PRAIRIEVIEW:
                logging.error(f"Expected ACK_CONNECT_PRAIRIEVIEW from harness pipe, received: {done}")
        return redirect(url_for('index'))


    @app.route('/load_decoder', methods=["POST"])
    def load_decoder():
        logging.info("UI Request: load decoder")
        if shared_dict['harness_busy'] == True:
            logging.warn("Harness is busy, ignoring request")
        else:
            decoder_name = request.form['decoderfile']
            instruction = (ProcessMessage.SEND_LOAD_DECODER, decoder_name)
            harness_pipe.send(instruction)
            done = harness_pipe.recv()
            if done != ProcessMessage.ACK_LOAD_DECODER:
                logging.error(f"Expected ACK_LOAD_DECODER, received: {done}")
        return redirect(url_for('index'))


    @app.route('/test_labview')
    def test_labview():
        logging.info("UI Request: test labview")
        if shared_dict['harness_busy'] == True:
            logging.warn("Harness is busy, ignoring request")
        else:
            instruction = (ProcessMessage.SEND_TEST_LABVIEW, 5)
            harness_pipe.send(instruction)
            done = harness_pipe.recv()
            if done != ProcessMessage.ACK_TEST_LABVIEW:
                logging.error(f"Expected ACK_TEST_LABVIEW, received: {done}")
    
        return redirect(url_for('index'))


    @app.route('/test_prairieview')
    def test_prairieview():
        duration_s = 10
        logging.info("UI Request: test imaging")
        if shared_dict['harness_busy'] == True or shared_dict['imaging_busy'] == True:
            logging.warn("ReTiCaDe is busy, ignoring request")
        else:
            instruction_1 = (ProcessMessage.SEND_TEST_PRAIRIEVIEW, duration_s)
            instruction_2 = (ProcessMessage.SEND_TEST_PRAIRIEVIEW, duration_s)
            harness_pipe.send(instruction_1)
            imaging_pipe.send(instruction_2)
        return redirect(url_for('index'))


    @app.route('/run_bmi', methods=["POST"])
    def run_bmi():
        duration_s = float(request.form['duration'])
        print(f"UI Request: Run BMI for {duration_s} s")
        if shared_dict['harness_busy'] == True or shared_dict['imaging_busy'] == True:
            logging.warn("ReTiCaDe is busy, ignoring request")
        else:
            instruction_1 = (ProcessMessage.SEND_RUN_BMI, duration_s)
            instruction_2 = (ProcessMessage.SEND_RUN_BMI, duration_s)
            imaging_pipe.send(instruction_1)
            time.sleep(2) # Let microscope warm up
            harness_pipe.send(instruction_2)
        return redirect(url_for('index'))
    
    return app
