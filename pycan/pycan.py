import can
import os
import sys
import configparser
import argparse

class Pycan:
    def __init__(self, CAN_CHANNEL_REC, PIPE_PATH = None):
        self.canbus = self._setup_bus(CAN_CHANNEL_REC)

        if PIPE_PATH:
            self.pipeout = self._create_pipe(PIPE_PATH)

    def _setup_bus(self, channel):
        try:
            self.bus = can.interface.Bus(channel=channel, bustype='socketcan')
            return self.bus

        except Exception as ex:
            return None

    def _create_pipe(self, pipe_path):
        if os.path.exists(pipe_path):
            self.pipeout = os.open(pipe_path, os.O_WRONLY)
        else:
            os.mkfifo(pipe_path)
            self.pipeout = os.open(pipe_path, os.O_WRONLY)

        return self.pipeout

    def send_message_on_pipe(self, msg, *args):

        self.sent_msg = ((int(msg.timestamp*1000)).to_bytes(6,'little')) + (msg.arbitration_id).to_bytes(4,'big') + (msg.dlc).to_bytes(1,'little') + msg.data
        d = os.write(self.pipeout, self.sent_msg)

    def listen_and_send(self, callback, *args):
        try:
            self.a_listener = can.BufferedReader()
            self.notifier = can.Notifier(self.canbus, [self.a_listener])

            while True:
                self.msg = self.a_listener.get_message(0.5)
                if self.msg:
                    callback(self.msg, args)

        except KeyboardInterrupt:
            os.close(self.pipeout)
            pass

        except (BrokenPipeError, IOError) as ex:
            pass

        finally:
            self.canbus.shutdown()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c")
    args = parser.parse_args()

    config = configparser.RawConfigParser()
    config.optionxform = str
    config.read(args.c)
    config_dict = dict(config.items('CONFIG'))

    pycan = Pycan(config_dict['CAN_CHANNEL_REC'], config_dict['PIPE_PATH'])
    pycan.listen_and_send(pycan.send_message_on_pipe)

if __name__ == "__main__":

    try:
        main()

    except KeyboardInterrupt:
        sys.exit(0)