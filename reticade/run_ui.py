import ui_server
import time
from multiprocessing import Process, Manager, Pipe
from interprocess_messages import ProcessMessage
import logging

logging.basicConfig(format='[%(asctime)s] [%(levelname)s] %(message)s',
                    datefmt='%H:%M:%S', level=logging.INFO)

def run_flask(harness_pipe, imaging_pipe, shared_dict):
    app = ui_server.create_flask_app(harness_pipe, imaging_pipe, shared_dict)
    app.run(debug=False)

def run_harness(flask_pipe, shared_dict):
    while True:
        shared_dict['harness_busy'] = False
        instruction = flask_pipe.recv()
        shared_dict['harness_busy'] = True
        instruction_id = instruction[0]
        if instruction_id == ProcessMessage.SEND_CONNECT_LABVIEW:
            labview_ip = instruction[1]
            shared_dict['labview_connected'] = True
            # TODO: implement me
            flask_pipe.send((ProcessMessage.ACK_CONNECT_LABVIEW))
        elif instruction_id == ProcessMessage.SEND_TEST_LABVIEW:
            # TODO: implement me
            flask_pipe.send((ProcessMessage.ACK_TEST_LABVIEW))
            pass
        elif instruction_id == ProcessMessage.SEND_RUN_BMI:
            duration = instruction[1]
            # TODO: implement me
            pass
        elif instruction_id == ProcessMessage.SEND_LOAD_DECODER:
            decoder_name = instruction[1]
            shared_dict['decoder'] = decoder_name
            # TODO: implement me
            flask_pipe.send((ProcessMessage.ACK_LOAD_DECODER))
        elif instruction_id == ProcessMessage.SEND_TEST_PRAIRIEVIEW:
            # TODO: implement me
            time.sleep(5)
            pass
        else:
            logging.error(f"Harness received unexpected instruction: {instruction}")
            pass



def run_imaging(flask_pipe, shared_dict):
    while True:
        shared_dict['imaging_busy'] = False
        instruction = flask_pipe.recv()
        shared_dict['imaging_busy'] = True
        instruction_id = instruction[0]
        if instruction_id == ProcessMessage.SEND_CONNECT_PRAIRIEVIEW:
            shared_dict['prairieview_connected'] = True
            # TODO: implement me
            logging.info("Conneting")
            flask_pipe.send((ProcessMessage.ACK_CONNECT_PRAIRIEVIEW))
        elif instruction_id == ProcessMessage.SEND_TEST_PRAIRIEVIEW:
            # TODO: implement me
            time.sleep(5)
            pass
        else:
            logging.error(f"Imaging process received unexpected instruction: {instruction}")

if __name__ == '__main__':
    with Manager() as manager:
        shared_dict = manager.dict()
        shared_dict['version'] = '2.0'
        shared_dict['imaging_busy'] = False
        shared_dict['harness_busy'] = False
        shared_dict['labview_connected'] = False
        shared_dict['prairieview_connected'] = False
        shared_dict['decoder'] = None


        flask_to_harness, harness_from_flask = Pipe()
        flask_to_imaging, imaging_from_flask = Pipe()

        flask_process = Process(target=run_flask, args=(flask_to_harness, flask_to_imaging, shared_dict))
        harness_process = Process(target=run_harness, args=(harness_from_flask, shared_dict))
        imaging_process = Process(target=run_imaging, args=(imaging_from_flask, shared_dict))
        harness_process.start()
        imaging_process.start()
        flask_process.start()
        harness_process.join()
        imaging_process.join()
        flask_process.join()
