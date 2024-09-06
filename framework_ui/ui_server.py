import threading
from ..interface.io_box_interface import PqaBoxInterface
from ..services.connection_box import ConnectionBox
from ..services.mini_jogger import MiniJogger
import socketserver
from ..services.power_supply import PowerSupply


class MyTCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = self.request.recv(1024).strip()
        data = data.decode("utf-8")

        splitted_data = data.split()

        # JOGGER
        if splitted_data[0] == 'JOGGER':
            # TODO Add enable, stop
            if splitted_data[1] == 'ONLINE':
                if self.server.my_jogger:
                    online_status = 'false'
                else:
                    online_status = 'true'
                self.request.sendall(online_status.encode('utf-8'))

            elif splitted_data[1] == 'ENABLE':
                self.server.my_jogger.enable()
            elif splitted_data[1] == 'DISABLE':
                self.server.my_jogger.disable()
            elif splitted_data[1] == 'STOP':
                self.server.my_jogger.set_speed(0)
            elif splitted_data[1] == 'SET_SPEED':
                self.server.my_jogger.set_speed(int(splitted_data[2]))

        # CONNECTION BOX

        elif splitted_data[0] == 'CBOX':
            if splitted_data[1] == 'ONLINE':
                if self.server.pqa_io_box:
                    online_status = 'false'
                else:
                    online_status = 'true'
                self.request.sendall(online_status.encode('utf-8'))

            elif splitted_data[1] == 'SET_IO':
                output_name = int(splitted_data[2])
                raw_state = splitted_data[3]

                if raw_state.lower() == 'true':
                    state = True
                else:
                    state = False
                self.server.pqa_io_box.set_io(output_name, state)

            elif splitted_data[1] == 'GET_VALUE':
                if splitted_data[2] == 'NAME':
                    cbox_name = self.server.pqa_io_box.cbox_name
                    cbox_name = cbox_name.to_bytes(2, 'big')
                    self.request.sendall(cbox_name)
                elif splitted_data[2] == 'SERIAL_NB':
                    cbox_serial = self.server.pqa_io_box.cbox_sn.encode('utf-8')
                    self.request.sendall(cbox_serial)
                elif splitted_data[2] == 'CBOX_FW':
                    hex_number = '{:04x}'.format(self.server.pqa_io_box.get_firmware_version())
                    self.request.sendall(hex_number.encode('utf-8'))

        elif splitted_data[0] == 'POWER_SUPPLY':
            # TODO Add set_voltage, enable, disable, set_current
            if splitted_data[1] == 'ONLINE':
                if self.server.power_supply:
                    online_status = 'false'
                else:
                    online_status = 'true'

                self.request.sendall(online_status.encode('utf-8'))

            elif splitted_data[1] == 'SET_CURRENT':
                self.server.power_supply.set_current_limit(float(splitted_data[2]))
            elif splitted_data[1] == 'SET_VOLTAGE':
                voltage = float(splitted_data[2])
                self.server.power_supply.set_voltage(voltage)
            elif splitted_data[1].lower() == 'off':
                self.server.power_supply.output_voltage(on_off='off')
            elif splitted_data[1].lower() == 'on':
                self.server.power_supply.output_voltage(on_off='ON')
            elif splitted_data[1] == 'GET_CURRENT':
                value = self.server.power_supply.get_current_limit()
                value_bytes = str(value).encode('utf-8')
                self.request.sendall(value_bytes)
        else:
            self.request.sendall(b'Command no recognize')


class GuiServer():
    def __init__(self, my_jogger: (MiniJogger, None) = None, pqa_io_box: (PqaBoxInterface, None) = None, power_supply: (PowerSupply, None) = None):
        self._host = "localhost"
        self._port = 9999
        self._my_jogger = my_jogger
        self._power_supply = power_supply
        self._pqa_io_box = pqa_io_box
        self._server = socketserver.TCPServer((self._host, self._port), MyTCPHandler)
        self._server.my_jogger = self._my_jogger
        self._server.pqa_io_box = self._pqa_io_box
        self._server.power_supply = self._power_supply
        self.powersupply_display_disable = False

    def _server_run(self):
        with socketserver.TCPServer((self._host, self._port), MyTCPHandler) as serverR:
            serverR.my_jogger = self._my_jogger
            serverR.pqa_io_box = self._pqa_io_box
            serverR.power_supply = self._power_supply
            serverR.serve_forever()

    def start_server(self):
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    def stop_server(self):
        if self._my_jogger:
            self._my_jogger.set_speed(0)

        if self._power_supply:
            self._power_supply.output_voltage('OFF')

        self._server.shutdown()


if __name__ == "__main__":
    connection_box = None
    jogger = None
    power_Supply = None

    # JOGGER
    try:
        my_jogger = MiniJogger('my name', 'COM3')
    except AssertionError as e:
        my_jogger = None

    # POWER SUPPLY
    try:
        power_supply = PowerSupply(power_supply_name='keithley_2281S-20-6', console_log=0, db_log=0)
    except AssertionError as e:
        power_supply = None

    # CONNECTION BOX
    try:
        cbox = ConnectionBox('my_cbox', 'TBL331')
    except AssertionError as e:
        cbox = None

    gui_server = GuiServer(my_jogger=my_jogger, power_supply=power_supply, pqa_io_box=cbox)
    gui_server.start_server()
