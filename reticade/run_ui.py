import time
import logging
import platform
from multiprocessing import Process, Manager, Pipe
import reticade.ui_server
from reticade.interprocess_messages import ProcessMessage

logging.basicConfig(format='[%(asctime)s] [%(levelname)s] %(message)s',
                    datefmt='%H:%M:%S', level=logging.INFO)

def run_flask(harness_pipe, imaging_pipe, udp_rx_pipe, shared_dict):
    app = reticade.ui_server.create_flask_app(harness_pipe, imaging_pipe, udp_rx_pipe, shared_dict)
    app.run(debug=False)

def run_harness(flask_pipe, shared_dict):
    shared_dict['harness_busy'] = True
    from reticade.interactive import Harness
    harness = Harness(enable_labview_debug=True)
    while True:
        shared_dict['harness_busy'] = False
        instruction = flask_pipe.recv()
        shared_dict['harness_busy'] = True
        instruction_id = instruction[0]
        if instruction_id == ProcessMessage.SEND_CONNECT_LABVIEW:
            labview_ip = instruction[1]
            shared_dict['labview_connected'] = True
            harness.set_link_ip(labview_ip)
            flask_pipe.send((ProcessMessage.ACK_CONNECT_LABVIEW))
        elif instruction_id == ProcessMessage.SEND_TEST_LABVIEW:
            num_fake_packets = instruction[1]
            test_data = [0 for i in range(num_fake_packets)]
            harness.test_link(test_data)
            flask_pipe.send((ProcessMessage.ACK_TEST_LABVIEW))
        elif instruction_id == ProcessMessage.SEND_CONNECT_PRAIRIEVIEW:
            harness.init_imaging()
            flask_pipe.send((ProcessMessage.ACK_CONNECT_PRAIRIEVIEW))
        elif instruction_id == ProcessMessage.SEND_RUN_BMI:
            duration = instruction[1]
            harness.run(stop_after_seconds=duration)
        elif instruction_id == ProcessMessage.SEND_LOAD_DECODER:
            decoder_name = instruction[1]
            shared_dict['decoder'] = decoder_name
            harness.load_decoder(f"decoders/{decoder_name}")
            flask_pipe.send((ProcessMessage.ACK_LOAD_DECODER))
        elif instruction_id == ProcessMessage.SEND_TEST_PRAIRIEVIEW:
            duration_s = instruction[1]
            harness.show_live_view(duration=duration_s)
        else:
            logging.error(f"Harness received unexpected instruction: {instruction}")
            

def run_udp_receiver(flask_pipe, shared_dict):
    from reticade.udp_controller_link import UdpMemshareReceiver
    receiver = UdpMemshareReceiver()
    while True:
        instruction = flask_pipe.recv()
        instruction_id = instruction[0]
        if instruction_id == ProcessMessage.SEND_CONNECT_LABVIEW:
            logging.info("Labview receiver configured")
            flask_pipe.send((ProcessMessage.ACK_CONNECT_LABVIEW))
            receiver.bind_and_run_forever()
        else:
            logging.error(f"UDP RX received unexpected instruction: {instruction}")


def run_imaging(flask_pipe, shared_dict):
    imaging = None
    import reticade.sapv_link
    while True:
        shared_dict['imaging_busy'] = False
        instruction = flask_pipe.recv()
        shared_dict['imaging_busy'] = True
        instruction_id = instruction[0]
        if instruction_id == ProcessMessage.SEND_CONNECT_PRAIRIEVIEW:
            shared_dict['prairieview_connected'] = True
            if platform.system() == 'Windows':
                imaging = reticade.sapv_link.StandaloneImager()
            else:
                imaging = reticade.sapv_link.TestImager()
            flask_pipe.send((ProcessMessage.ACK_CONNECT_PRAIRIEVIEW))
        elif instruction_id == ProcessMessage.SEND_TEST_PRAIRIEVIEW:
            if imaging is None:
                logging.error("Request to run liveview when imaging not configured")
            else:
                duration_s = instruction[1]
                imaging.run_liveview(duration_s)
        elif instruction_id == ProcessMessage.SEND_RUN_BMI:
            duration_s = instruction[0]
            if imaging is None:
                logging.error("Request to run timeseries when imaging not configured")
            else:
                duration_s = instruction[1]
                imaging.run_timeseries(duration_s)
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
        flask_to_udp, udp_from_flask = Pipe()

        udp_rx_process = Process(target=run_udp_receiver, args=(udp_from_flask, shared_dict))
        flask_process = Process(target=run_flask, args=(flask_to_harness, flask_to_imaging, flask_to_udp, shared_dict))
        harness_process = Process(target=run_harness, args=(harness_from_flask, shared_dict))
        imaging_process = Process(target=run_imaging, args=(imaging_from_flask, shared_dict))
        udp_rx_process.start()
        harness_process.start()
        imaging_process.start()
        flask_process.start()
        harness_process.join()
        imaging_process.join()
        flask_process.join()
        udp_rx_process.join()
