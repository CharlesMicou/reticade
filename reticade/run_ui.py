import ui_server
import time
from multiprocessing import Process, Manager, Pipe

def run_flask(harness_pipe, imaging_pipe, shared_dict):
    app = ui_server.create_flask_app(harness_pipe, imaging_pipe, shared_dict)
    app.run(debug=False)

def run_harness(flask_pipe, shared_dict):
    while True:
        shared_dict['harness_busy'] = False
        instruction = flask_pipe.recv()
        shared_dict['harness_busy'] = True
        
        time.sleep(5)
        shared_dict['labview_connected'] = True
        flask_pipe.send("Done")


def run_imaging(flask_pipe, shared_dict):
    pass

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
        flask_process.start()
        harness_process.start()
        harness_process.join()
        flask_process.join()
