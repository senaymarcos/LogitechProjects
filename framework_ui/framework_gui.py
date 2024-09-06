import math
import PySimpleGUI as sg
import socket
from pypqa.services.connection_box import ConnectionBox


#from ..services.connection_box import ConnectionBox
#from tools.python_pqa_libs.pypqa.services.connection_box import ConnectionBox


class Client:
    def __init__(self, ip_adress, port):
        self.ip_adress = ip_adress
        self.port = port

    def set_send_data(self, data, read_response=False):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Connect to server and send data
            sock.connect((self.ip_adress, self.port))
            sock.sendall(bytes(data + "\n", "utf-8"))

            if read_response:
                data = sock.recv(1024).strip()
                data = data.decode("utf-8")
                return data

    def send_command(self, device: str, function: str, **kwargs):
        output_number = kwargs.get('output_number', '')
        state = kwargs.get('state', '')
        speed = kwargs.get('speed', '')
        value = kwargs.get('value', '')

        data = device + ' ' + function + ' ' + str(output_number) + ' ' + str(state) + ' ' + str(speed) + ' ' + str(
            value)

        print(data)
        try:
            self.set_send_data(data)
        except:
            print(f'failed to send cmd: {device}')
            sg.popup('Connection Error', f'Failed to send command to the   {device}', background_color='#FF4C4C',
                     font=('Arial', 13))

    def read_command(self, device: str, function: str, **kwargs):
        sub_function = kwargs.get('sub_function', '')
        id = kwargs.get('id', '')
        firmware_version = kwargs.get('firmware_version', '')

        data = device + ' ' + function + ' ' + sub_function + ' ' + str(id) + ' ' + str(firmware_version)

        print(data)

        try:
            read_data = self.set_send_data(data, read_response=True)
        except:
            read_data = None
            print(f'failed to read cmd: {device}')

        return read_data


class Dashboard:
    """
        Initialise the Dashboard for Connection Box, Power Supply, Jogger.

        Args:

    """
    power_supply_status: bool

    def __init__(self, ip_adress, port):
        self.keys_list = None
        self.block_1 = None
        self.window = None
        self.jogger_display_disable = False
        self.powersupply_display_disable = False
        self.cbox_display_disable = False
        self.client = Client(ip_adress=ip_adress, port=port)
        self.id = self.client.read_command(device='CBOX', function='GET_VALUE', sub_function='ID')
        self.serial_sn = self.client.read_command(device='CBOX', function='GET_VALUE', sub_function='SERIAL_NB')
        self.cbox_firmware = self.client.read_command(device='CBOX', function='GET_VALUE', sub_function='CBOX_FW')

        # POWER SUPPLY

        self.power_supply_status = self.client.read_command(device='POWER_SUPPLY', function='ONLINE')
        if self.power_supply_status == 'false':
            self.power_supply_status = False
        else:
            self.power_supply_status = True

        # CONNECTION BOX

        self.cbox_status = self.client.read_command(device='CBOX', function='ONLINE')
        if self.cbox_status == 'false':
            self.cbox_status = False
        else:
            self.cbox_status = True

        # JOGGER

        self.jogger_status = self.client.read_command(device='JOGGER', function='ONLINE')
        if self.jogger_status == 'false':
            self.jogger_status = False
        else:
            self.jogger_status = True

        self.theme_dict = {'BACKGROUND': '#f5e6eb',
                           'TEXT': '#090a0a',
                           'INPUT': '#F2EFE8',
                           'TEXT_INPUT': '#000000',
                           'SCROLL': '#F2EFE8',
                           'BUTTON': ('#000000', '#94888c', '#e884a4'),
                           'PROGRESS': ('#FFFFFF', '#C7D5E0'),
                           'BORDER': 1, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0}

        sg.LOOK_AND_FEEL_TABLE['Dashboard'] = self.theme_dict
        sg.theme('Dashboard')

        self.BORDER_COLOR = '#c9bdc1'
        self.BPAD_TOP = ((20, 20), (20, 10))
        self.BPAD_LEFT = ((20, 10), (0, 10))
        self.BPAD_LEFT_INSIDE = (10, 10)
        self.BPAD_RIGHT = ((10, 20), (10, 20))
        self.number_columns_typing = 7
        self.number_row_typing = 4
        self.val = 0
        self.speed_value = 0
        self.checkbox_state = False
        self.cbox_dll = '1.0.0.6'
        self.board_rev = 'n/a'
        self.col = 4
        self.row = 4
        self.flag = False
        self.current_index = 0
        self.prev_key = None

        self.active = {'ANALOG9': ConnectionBox.Outputs.analog_switch_9,
                       'ANALOG10': ConnectionBox.Outputs.analog_switch_10,
                       'ANALOG11': ConnectionBox.Outputs.analog_switch_11,
                       'ANALOG12': ConnectionBox.Outputs.analog_switch_12,
                       'ANALOG13': ConnectionBox.Outputs.analog_switch_9,
                       'ANALOG14': ConnectionBox.Outputs.analog_switch_10,
                       'ANALOG15': ConnectionBox.Outputs.analog_switch_11,
                       'ANALOG16': ConnectionBox.Outputs.analog_switch_12}

        self.actuator_dict_1 = {'TYPING0_1': ConnectionBox.Outputs.typing_actuator_1,
                                'TYPING0_2': ConnectionBox.Outputs.typing_actuator_2,
                                'TYPING0_3': ConnectionBox.Outputs.typing_actuator_3,
                                'TYPING0_4': ConnectionBox.Outputs.typing_actuator_4,
                                'TYPING0_5': ConnectionBox.Outputs.typing_actuator_5,
                                'TYPING0_6': ConnectionBox.Outputs.typing_actuator_6,
                                'TYPING0_7': ConnectionBox.Outputs.typing_actuator_7,
                                'TYPING0_8': ConnectionBox.Outputs.typing_actuator_8
                                }
        self.actuator_dict_2 = {'TYPING1_8': ConnectionBox.Outputs.typing_actuator_1,
                                'TYPING1_9': ConnectionBox.Outputs.typing_actuator_2,
                                'TYPING1_10': ConnectionBox.Outputs.typing_actuator_3,
                                'TYPING1_11': ConnectionBox.Outputs.typing_actuator_4,
                                'TYPING1_12': ConnectionBox.Outputs.typing_actuator_5,
                                'TYPING1_13': ConnectionBox.Outputs.typing_actuator_6,
                                'TYPING1_14': ConnectionBox.Outputs.typing_actuator_7
                                }
        self.actuator_dict_3 = {'TYPING2_15': ConnectionBox.Outputs.typing_actuator_1,
                                'TYPING2_16': ConnectionBox.Outputs.typing_actuator_2,
                                'TYPING2_17': ConnectionBox.Outputs.typing_actuator_3,
                                'TYPING2_18': ConnectionBox.Outputs.typing_actuator_4,
                                'TYPING2_19': ConnectionBox.Outputs.typing_actuator_5,
                                'TYPING2_20': ConnectionBox.Outputs.typing_actuator_6,
                                'TYPING2_21': ConnectionBox.Outputs.typing_actuator_7
                                }
        self.actuator_dict_4 = {'TYPING3_22': ConnectionBox.Outputs.typing_actuator_1,
                                'TYPING3_23': ConnectionBox.Outputs.typing_actuator_2,
                                'TYPING3_24': ConnectionBox.Outputs.typing_actuator_3,
                                'TYPING3_25': ConnectionBox.Outputs.typing_actuator_4,
                                'TYPING3_26': ConnectionBox.Outputs.typing_actuator_5,
                                'TYPING3_27': ConnectionBox.Outputs.typing_actuator_6,
                                'TYPING3_28': ConnectionBox.Outputs.typing_actuator_7
                                }

        self.event_dict = {
            'ERROR': ConnectionBox.Outputs.ld3,
            'LD0': ConnectionBox.Outputs.ld0,
            'LD1': ConnectionBox.Outputs.ld1,
            'LD2': ConnectionBox.Outputs.ld2,
            '-OUT1-': ConnectionBox.Outputs.power_output_1,
            '-OUT2-': ConnectionBox.Outputs.power_output_2,
            '-OUT3-': ConnectionBox.Outputs.power_output_3,
            '-OUT4-': ConnectionBox.Outputs.power_output_4,
            'ANALOG1': ConnectionBox.Outputs.analog_switch_1,
            'ANALOG2': ConnectionBox.Outputs.analog_switch_2,
            'ANALOG3': ConnectionBox.Outputs.analog_switch_3,
            'ANALOG4': ConnectionBox.Outputs.analog_switch_4,
            'ANALOG6': ConnectionBox.Outputs.analog_switch_6,
            'ANALOG5': ConnectionBox.Outputs.analog_switch_5,
            'ANALOG7': ConnectionBox.Outputs.analog_switch_7,
            'ANALOG8': ConnectionBox.Outputs.analog_switch_8,
            'USB_1': ConnectionBox.Outputs.usb_board_1,
            'USB_2': ConnectionBox.Outputs.usb_board_2,

        }
        self.all_output_dict = {}
        self.all_output_dict.update(self.active)
        self.all_output_dict.update(self.actuator_dict_1)
        self.all_output_dict.update(self.actuator_dict_2)
        self.all_output_dict.update(self.actuator_dict_3)
        self.all_output_dict.update(self.actuator_dict_4)
        self.all_output_dict.update(self.event_dict)

        self.keys = {'ANALOG9': 'ANALOG13', 'ANALOG13': 'ANALOG9', 'ANALOG10': 'ANALOG14', 'ANALOG14': 'ANALOG10',
                     'ANALOG11': 'ANALOG15', 'ANALOG15': 'ANALOG11', 'ANALOG12': 'ANALOG16',
                     'ANALOG16': 'ANALOG12'}
        self.list_mux_inactive = ['TYPING0_8', '-OUT3-', '-OUT4-']
        self.list_one = ['TYPING0_1', 'TYPING0_2', 'TYPING0_3', 'TYPING0_4', 'TYPING0_5', 'TYPING0_6', 'TYPING0_7',
                         'TYPING0_8']
        self.list_two = ['TYPING1_8', 'TYPING1_9', 'TYPING1_10', 'TYPING1_11', 'TYPING1_12', 'TYPING1_13',
                         'TYPING1_14']
        self.list_three = ['TYPING2_15', 'TYPING2_16', 'TYPING2_17', 'TYPING2_18', 'TYPING2_19', 'TYPING2_20',
                           'TYPING2_21']
        self.list_four = ['TYPING3_22', 'TYPING3_23', 'TYPING3_24', 'TYPING3_25', 'TYPING3_26', 'TYPING3_27',
                          'TYPING3_28']
        self.list_mux_actives = self.list_two + self.list_three + self.list_four

    # TODO convert to function

    def start_ui(self):
        self.define_layout()
        self.event_active()

    def checkbox_format(self, x):
        """
            Convert a number to a two-digit string and add a space character.
            Args:
                x (int): the number to be formatted.
            Returns:
                str: the formatted string with two digits and a space character.
        """
        return f"{x:02d}      "

    def invert_format(self, x):
        """
             Convert a number to a two-digit string and add a space character.
            Args:
                x (int): the number to be formatted.
            Returns:
                str: the formatted string with two digits and a space character.
        """
        return f"{x:02d} inv "

    """
        REST IN PEACE MY LOVELY FUNCTION
    """

    # power supply
    def max_current(self, x):
        """
            Set the max current on the power supply.

            Args:
                x(str): The current value, then convert into the float.
        """
        try:
            self.client.send_command(device='POWER_SUPPLY', function='SET_CURRENT', value=x)

        except:
            self.window['CURRENT_INPUT'].update(value='enter a number please')

    def set_voltage(self, value_input):
        """
            Set the voltage on the power supply.

            Args:
                value_input(str) : The voltage value to set on power supply, then convert into the float.

        """
        try:
            self.client.send_command(device='POWER_SUPPLY', function='SET_VOLTAGE', value=value_input)

        except AssertionError:
            self.window['INPUT_VOLTAGE'].update(value='enter a number please')

    def get_current(self):
        """
            get current limit on the power supply
        """
        if self.powersupply_display_disable:
            return ""
        else:
            self.current_value = self.client.read_command('POWER_SUPPLY', 'GET_CURRENT')
            return self.current_value

    def define_layout(self):
        """
            Manage the ConnectionBox, PowerSupply and Jogger UI part.
        """
        # Connection BOx UI
        col1 = sg.Frame('C-Box FW/ EEPROM', [
            [
                sg.Text('Serial'),
                sg.Input(key='-SERIAL-', default_text=self.serial_sn, size=(10, 1), disabled=self.cbox_status),
                sg.Text('CBox Dll'),
                sg.Input(key='-CBOX-DLL-', default_text=self.cbox_dll, size=(10, 1),
                         disabled=self.cbox_status)],
            [sg.Text('Board rev'),
             sg.Input(key='BOARD-REV', default_text=self.board_rev, size=(10, 1), disabled=self.cbox_status),
             sg.Text('CBox FW'),
             sg.Input(key='-CBOX_FW-', default_text=self.cbox_firmware, disabled=self.cbox_status,
                      size=(10, 1))]],
                        size=(350, 40), expand_x=True, pad=(20, 3))

        col2 = sg.Frame('LED',
                        [[sg.Column(
                            [[sg.Checkbox('LD0', key='LD0', enable_events=True, disabled=self.cbox_status),
                              sg.Checkbox('LD1', key='LD1', enable_events=True, disabled=self.cbox_status),
                              sg.Checkbox('LD2', key='LD2', enable_events=True, disabled=self.cbox_status),
                              sg.Checkbox('ERROR', text_color='red', key='ERROR', enable_events=True,
                                          disabled=self.cbox_display_disable)]],
                            size=(350, 30))]], expand_x=True, pad=(20, 2))

        col3 = sg.Frame('USB Plug/Unplug',
                        [[sg.Column([[sg.Checkbox('unplug 1', key='USB_1', enable_events=True,
                                                  disabled=self.cbox_status),
                                      sg.Checkbox('unplug 2', key='USB_2', enable_events=True,
                                                  disabled=self.cbox_status)]],
                                    size=(350, 30))]], expand_x=True, pad=(20, 2))

        col4 = sg.Frame('Power out', [
            [sg.Column([[sg.Checkbox('out 1', key='-OUT1-', enable_events=True, disabled=self.cbox_status),
                         sg.Checkbox('out 2', key='-OUT2-', enable_events=True, disabled=self.cbox_status),
                         sg.Checkbox('out 3', key='-OUT3-', enable_events=True, disabled=self.cbox_status),
                         sg.Checkbox('out 4', key='-OUT4-', enable_events=True, disabled=self.cbox_status)]],
                       size=(350, 30))]], expand_x=True, pad=(20, 2))

        col5 = sg.Frame('Analog switches', [
            [sg.Column([[sg.Checkbox(
                self.checkbox_format((j + 1) + 4 * i) if i <= 2 else
                self.invert_format((j + 1) + 4 + self.col),
                key=f"ANALOG{i * 4 + 1 + j}", enable_events=True, disabled=self.cbox_status,
                default=True if i * 4 + 1 + j > 12 else False)
                for j in range(self.col)] for i in range(self.row)],
                size=(350, 120))]], expand_x=True, pad=(20, 2))

        typing_columns = []
        for i in range(self.number_row_typing):
            row = []
            for j in range(self.number_columns_typing + 1):
                if (j + 1) + self.number_columns_typing * i <= 9:
                    if i == 1 and j <= 1:
                        row.append(
                            (sg.Checkbox('0' + str((j + 1) + self.number_columns_typing * i), enable_events=True,
                                         disabled=True,
                                         key=f'TYPING{i}_{(j + 1) + self.number_columns_typing * i}')))
                    else:
                        row.append(
                            (sg.Checkbox('0' + str((j + 1) + self.number_columns_typing * i), enable_events=True,
                                         disabled=self.cbox_status,
                                         key=f'TYPING{i}_{(j + 1) + self.number_columns_typing * i}')))
                elif j == self.number_columns_typing:
                    row.append(sg.Text(''))
                else:
                    row.append(
                        (sg.Checkbox(str((j + 1) + self.number_columns_typing * i), enable_events=True, disabled=True,
                                     key=f'TYPING{i}_{(j + 1) + self.number_columns_typing * i}')))
            typing_columns.append(row)
        typing_layout = [[sg.Column(typing_columns, size=(400, 120))],
                         [sg.Column([[sg.Button('Toggle next output', disabled=self.cbox_status),
                                      sg.Button('Toggle all outputs', disabled=self.cbox_status),
                                      sg.Checkbox('Multiplexer',
                                                  key='MUX_BUTTON',
                                                  enable_events=True, disabled=self.cbox_status)]],
                                    size=(400, 35))]]

        col6 = sg.Frame('Typing', typing_layout, expand_x=True, pad=(20, 10))

        self.block_1 = [[sg.Text('CONNECTION BOX', font='Any 10', pad=(10, 3), )],
                        [sg.HorizontalSeparator()], [col1], [col2], [col3], [col4], [col5], [col6]]

        # jogger
        col_2_1 = sg.Frame('',
                           [[sg.Column([[sg.Button('Enable', key='ENABLE_JOGGER', disabled=self.jogger_status),
                                         sg.Button('Disable', key='DISABLE_JOGGER',
                                                   disabled=self.jogger_status, button_color='#f03a46')]],
                                       size=(280, 30))]], expand_x=True, pad=(20, 3))

        # range of speed is here
        col_2_2 = sg.Frame('Speed',
                           [[sg.Column(
                               [[sg.Slider(range=(-3000, 3000), default_value=self.val, size=(20, 13), orientation="h",
                                           enable_events=True, key="SLIDER", disabled=self.jogger_status),
                                 sg.Button('Stop', button_color='#f03a46', key='STOP_SLIDER',
                                           disabled=self.jogger_status)]])]], expand_x=True,
                           pad=(15, 0))

        col_2_3 = sg.Frame('Position', [[sg.Column([[sg.Input(size=(10, 1), disabled=self.jogger_status),
                                                     sg.Button('Move', key='MOVE_RELATIVE',
                                                               disabled=self.jogger_status)]],
                                                   size=(280, 30))]], expand_x=True, pad=(20, 3))

        block_2 = [[sg.Text('JOGGER', font='Any 10', pad=(20, 3))],
                   [sg.HorizontalSeparator()],
                   [col_2_1], [col_2_2],
                   [col_2_3]]

        # power supply
        col_3_1 = sg.Frame('',
                           [[sg.Column([[sg.Text('Output'),
                                         sg.Button('On', key='ON', disabled=self.power_supply_status),
                                         sg.Button('Off', key='OFF', button_color='#f03a46',
                                                   disabled=self.power_supply_status)]],
                                       size=(250, 30))]], expand_x=True, pad=(20, 3))
        col_3_2 = sg.Frame('', [
            [sg.Column([[sg.Input(size=(18, 1), key='INPUT_VOLTAGE', disabled=self.power_supply_status),
                         sg.Button('Set Voltage', key='SET_VOLTAGE', disabled=self.power_supply_status)]],
                       size=(250, 30))]], expand_x=True, pad=(20, 3))

        col_3_3 = sg.Frame('', [
            [sg.Column([
                [sg.Input(size=(18, 1), key='CURRENT_INPUT',
                          disabled=self.power_supply_status, default_text=self.get_current()),
                 sg.Button('Set Current', key='SET_CURRENT', disabled=self.power_supply_status)]],
                size=(250, 50))]], expand_x=True, pad=(20, 3))

        block_3 = [[sg.Text('POWER SUPPLY', font='Any 10', pad=(20, 3))],
                   [sg.HorizontalSeparator()],
                   [col_3_1],
                   [col_3_2], [col_3_3]]
        layout = [
            [sg.Column([[sg.Column(self.block_1, size=(460, 640), pad=self.BPAD_LEFT_INSIDE)]
                        ], pad=self.BPAD_LEFT, background_color=self.BORDER_COLOR),
             sg.Column(block_2, size=(350, 640), pad=self.BPAD_RIGHT),
             sg.Column(block_3, size=(350, 640), pad=self.BPAD_RIGHT)]]

        self.window = sg.Window('Control Device', layout, margins=(3, 3), background_color=self.BORDER_COLOR)

    def handle_analog_event(self, key, already_set):
        """
            handle the analog event for analog part between 9-12,
            and inactive pair 9inv-12inv.

            Args :
                key(str) : the selected key that was clicked.
                already_set(bool) : The current state of checkbox(ON or OFF).
        """

        if not (key in self.keys):
            return

        if already_set:
            self.switch_on(key)
            if self.prev_key:
                self.window[self.prev_key].update(value=0)
        else:
            self.switch_on(self.keys[key])

    def checkbox_grayed_out(self, values, current_key):
        """
            Manages the change of output levels depending on whether the "MUX_BUTTON" key is activated or not.
            If the "MUX_BUTTON" is activated, the function updates the state of the current key

            Args:
                values (dict): A dictionary containing the current values of the window.
                current_key (str): The current key that is being processed.
        """
        if self.current_index == len(self.keys_list) - 1:
            self.current_index = -1
        elif values['MUX_BUTTON'] and current_key in ['-OUT3-', '-OUT4-', 'TYPING0_8']:
            self.window[self.prev_key].update(value=0)
            self.prev_key = current_key

        elif not values['MUX_BUTTON'] and current_key in self.list_mux_actives:
            self.window[self.prev_key].update(value=0)
            self.prev_key = current_key
            self.current_index = -1
        else:
            self.handle_regular_events(current_key, True)
            self.window[current_key].update(value=1)
            if self.prev_key:
                self.window[self.prev_key].update(value=0)
                self.handle_regular_events(self.prev_key, False)
            self.prev_key = current_key

    def toggle_button_function(self, values):
        """
               It takes in a dictionary of values that represents the current state of the UI,
               and updates the state based on the user's actions.

               Args:
                 values (dict): A dictionary of values representing the current state of the UI.
        """
        self.keys_list = list(values.keys())[5:61]
        current_key = self.keys_list[self.current_index]

        if current_key in self.active.keys():
            self.handle_analog_event(current_key, not values[current_key])
        else:
            self.checkbox_grayed_out(values, current_key)
        self.current_index += 1

    def switch_on(self, key):
        """
            Activates the selected key for analog_pairs key and sets
            the input/output status of the corresponding connection box.

            Args:
                key(str) :  the selected key that was clicked.
        """

        self.window[key].update(value=1)
        self.window[self.keys[key]].update(value=0)
        self.client.send_command(device='CBOX', function='SET_IO', output_number=self.active[key],
                                 state=True)

    def handle_regular_events(self, event, state):
        """
            Activates the selected key-USB , LED , ANALOG, POWER-OUT and
            sets the input/output status corresponding connection box.

            Args:
                event(str): selected key that was clicked.
                state (bool): The current state of the checkbox (checked or unchecked).
        """
        if event in self.event_dict:
            output_name = self.event_dict[event]

            # TODO rework
            if isinstance(output_name, tuple):
                func, args = output_name
                print(output_name)
                func(*args)
            else:
                self.checkbox_state = state
                if 'ANALOG' in event:
                    self.client.send_command(device='CBOX', function='SET_IO', output_number=output_name,
                                             state=self.checkbox_state)
                elif '-OUT' in event:
                    self.client.send_command(device='CBOX', function='SET_IO', output_number=output_name,
                                             state=self.checkbox_state)
                elif 'USB_' in event:
                    self.client.send_command(device='CBOX', function='SET_IO', output_number=output_name,
                                             state=self.checkbox_state)
                else:
                    self.client.send_command(device='CBOX', function='SET_IO', output_number=output_name,
                                             state=not self.checkbox_state)

    def handle_typing(self, event, values):
        """
             Activates the selected key for TYPING, add multiplexer and
             sets the input/output status corresponding connection box.

             Args:
                event(str) : selected key that was clicked.
                values(dict) : A dictionary containing the current values of the window.
        """

        pow_out_converter = [[False, False], [False, True], [True, False], [True, True]]

        current_typing_state = values[event]
        typing_nb = event.split('_')[1]
        typing_nb_int = int(typing_nb)
        left_over = math.floor(typing_nb_int / 7)
        mod = typing_nb_int % 7

        if 'TYPING0_8' in event:
            left_over = 0

        if mod == 0:
            left_over -= 1

        power_out = pow_out_converter[left_over]
        out3 = power_out[0]
        out4 = power_out[1]
        ''' key_found = matching_dict.get(event)'''
        if left_over:
            if current_typing_state:
                if out3:
                    self.window['-OUT3-'].update(value=1)
                    self.client.send_command(device='CBOX', function='SET_IO',
                                             output_number=ConnectionBox.Outputs.power_output_3, state=out3)
                else:
                    self.window['-OUT3-'].update(value=0)
                    self.client.send_command(device='CBOX', function='SET_IO',
                                             output_number=ConnectionBox.Outputs.power_output_3, state=out3)

                if out4:
                    self.window['-OUT4-'].update(value=1)
                    self.client.send_command(device='CBOX', function='SET_IO',
                                             output_number=ConnectionBox.Outputs.power_output_4, state=out4)
                else:
                    self.window['-OUT4-'].update(value=0)
                    self.client.send_command(device='CBOX', function='SET_IO',
                                             output_number=ConnectionBox.Outputs.power_output_4, state=out4)
            else:
                self.window['-OUT3-'].update(value=0)
                self.window['-OUT4-'].update(value=0)
                self.client.send_command(device='CBOX', function='SET_IO',
                                         output_number=ConnectionBox.Outputs.power_output_3, state=False)
                self.client.send_command(device='CBOX', function='SET_IO',
                                         output_number=ConnectionBox.Outputs.power_output_4, state=False)
        else:
            res = typing_nb_int
            typing_actuator_list = list(self.actuator_dict_1.values())
            self.client.send_command(device='CBOX', function='SET_IO', output_number=typing_actuator_list[res - 1],
                                     state=out3)
            self.client.send_command(device='CBOX', function='SET_IO', output_number=typing_actuator_list[res - 1],
                                     state=out4)

    def mux_event(self, value):
        """
            Manage the change of disabled some checkbox according the MUX_BUTTON value.

            Args:
                value(bool): The current state of the Multiplexer checkbox (checked or unchecked).
        """
        if value:
            for i in self.list_mux_inactive:
                self.window[i].update(disabled=True)
            for j in self.list_mux_actives:
                self.window[j].update(disabled=False)
        elif not value:
            for j in self.list_mux_actives:
                self.window[j].update(disabled=True)
            for i in self.list_mux_inactive:
                self.window[i].update(disabled=False)

    def event_active(self):
        """
            Runs UI application that listens for events and performs actions based on the event and values.
        """
        while True:  # Event Loop
            event, values = self.window.read(timeout=300)

            # TODO to put in function using it

            if event != '__TIMEOUT__':

                if event in (sg.WIN_CLOSED, 'Exit'):
                    break

                if 'TYPING' in event:
                    self.handle_typing(event, values)

                if event == 'Toggle all outputs' and not self.flag:
                    self.flag = True

                elif event == 'Toggle all outputs' and self.flag:
                    self.flag = False

                elif event == 'Toggle next output':
                    self.toggle_button_function(values)

                elif event == 'MUX_BUTTON':
                    self.mux_event(values['MUX_BUTTON'])

                # JOGGER
                elif event == 'ENABLE_JOGGER':
                    self.client.send_command(device='JOGGER', function='ENABLE')

                elif event == 'DISABLE_JOGGER':
                    self.client.send_command(device='JOGGER', function='DISABLE')
                    self.window['SLIDER'].update(value=0)

                elif event == 'SLIDER':
                    slider_value = values['SLIDER']
                    slider_value_int = int(slider_value)
                    self.client.send_command(device='JOGGER', function='SET_SPEED', speed=slider_value_int)

                elif event == 'STOP_SLIDER':
                    self.client.send_command(device='JOGGER', function='SET_SPEED', speed=0)
                    self.window['SLIDER'].update(value=0)

                # power_supply event
                elif event == 'OFF':
                    self.client.send_command(device='POWER_SUPPLY', function='off')

                elif event == 'ON':
                    self.client.send_command(device='POWER_SUPPLY', function='on')

                elif event == 'SET_VOLTAGE':
                    self.set_voltage(values['INPUT_VOLTAGE'])

                elif event == 'SET_CURRENT':
                    self.max_current(values['CURRENT_INPUT'])
                    self.window['CURRENT_INPUT'].update(value=self.get_current())

                else:
                    # connection box
                    if event in values:
                        self.handle_analog_event(event, values[event])
                    self.handle_regular_events(event, values[event])
            elif self.flag:
                self.toggle_button_function(values)
        self.window.close()


if __name__ == "__main__":
    new_window = Dashboard(ip_adress='localhost', port=9999)
    new_window.define_layout()
    new_window.event_active()
