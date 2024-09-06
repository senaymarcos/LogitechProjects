import PySimpleGUI as sg
from time import sleep
from python_pqa_libs.pypqa.services.host_events_client import HostEventsClient
# from python_pqa_libs.pypqa.services import roller_server
from python_pqa_libs.pypqa.services.motor_controller import MaxonEpos2, FaulhaberMcV3
# from python_pqa_libs.pypqa.services.roller_server import RollerServer


import time
import math


class Roller:
    """
        Initialise the Roller for Roller UI.
        Args:
    """

    def __init__(self, usb_port, D2):
        self.velocity = None
        self.usb_port = usb_port
        self.window = None
        self.MaxonEpos2 = MaxonEpos2()
        self.Faulhaber = FaulhaberMcV3(self.usb_port)
        self.event_server = HostEventsClient(server_type='raw_input')
        self.D2 = D2
        self.Faulhaber.set_mode(FaulhaberMcV3.OperationMode.TORQUE)
        self.Faulhaber.switch_drive(enabled=True)
        self.theme_dict = {'BACKGROUND': '#B8BBC1',
                           'TEXT': '#090a0a',
                           'INPUT': '#F2EFE8',
                           'TEXT_INPUT': '#000000',
                           'SCROLL': '#F2EFE8',
                           'BUTTON': ('white', '#30D5C8', '#A49393'),
                           'PROGRESS': ('#5A5E68', '#5A5E68'),
                           'BORDER': 1, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0}

        sg.LOOK_AND_FEEL_TABLE['Dashboard'] = self.theme_dict
        sg.theme('Dashboard')

        self.default_angular_speed = 300
        self.default_angular_angle = '360 °'
        self.default_press_value = -300
        self.BORDER_COLOR = 'black'
        self.BPAD_TOP = ((20, 20), (20, 10))
        self.BPAD_LEFT = ((20, 10), (0, 10))
        self.BPAD_LEFT_INSIDE = (10, 10)
        self.BPAD_RIGHT = ((10, 20), (10, 20))

    def roller_layout(self):
        """
                Manage the  MaxonEpos2, FaulhaberMcV3 UI part.
        """
        # Wheel Control
        wheel_layout = sg.Frame('',
                                [
                                    [sg.Text('Angular Speed', pad=(10, 10), size=(15, 1), expand_x=True, expand_y=True),
                                     sg.Input(size=(15, 2), pad=(20, 10), default_text=self.default_angular_speed,
                                              expand_x=True, expand_y=True,
                                              key='ANGULAR_SPEED')],

                                    [sg.Text('Angular Position', size=(15, 1), expand_x=True, pad=(10, 10),
                                             expand_y=True),
                                     sg.Input(size=(15, 2), expand_x=True, pad=(20, 10), expand_y=True,
                                              default_text=self.default_angular_angle, key='ANGULAR_POSITION')],
                                    [sg.Text('Mouse Diameter (mm)', expand_x=True, pad=(10, 10), size=(15, 1),
                                             expand_y=True),
                                     sg.Input(size=(15, 2), expand_x=True, pad=(20, 10), expand_y=True,
                                              key='D1_DIAMETER')],
                                    [sg.Text('Bench Movement', expand_x=True, pad=(10, 10), size=(15, 1),
                                             expand_y=True, ),
                                     sg.Input(size=(15, 2), expand_x=True, pad=(20, 10), expand_y=True,
                                              key='D1_MOVEMENT')],
                                    [sg.Button('START', key='START_WHEEL', enable_events=True, pad=(20, 10))],
                                    {sg.Column([
                                        [sg.Text('Timer')],
                                        [sg.Input(size=(18, 2),
                                                  justification='center', key='timer_text', pad=(20, 10))],
                                    ],
                                        element_justification='center',
                                    )}
                                ],
                                size=(400, 400), expand_x=True, pad=(60, 30), element_justification='center')

        block_wheel = [[sg.Image('C:/Users/satli/Desktop/imag.png')],
                       [sg.Text('WHEEL CONTROL', font='Any 10', pad=(10, 3), justification='center')], [wheel_layout]]

        # TRAY CONTROL
        tray_layout = sg.Frame('',
                               [[sg.Checkbox('Enable Drive', pad=(20, 20), default=True, key='ENABLE_DRIVE')],
                                [sg.Text('Tray Pressure', pad=(20, 20))],
                                [sg.Text('← closer mouse', text_color='white', background_color='black', pad=(30, 0)),
                                 sg.Text('move away mouse → ', text_color='white', background_color='black',
                                         pad=(30, 0))],
                                [sg.Slider(range=(-600, 600), default_value=0, size=(30, 13), orientation="h",
                                           enable_events=True, key="TRAY_SLIDER", pad=(10, 0))],
                                [sg.Button('Stop', key='STOP_SLIDER', size=(4, 2), pad=(0, 10))]
                                ], element_justification='center',
                               size=(400, 400),
                               expand_x=True, pad=(20, 3), )

        block_tray = [[sg.Text('TRAY CONTROL', font='Any 10', pad=(20, 3))],
                      [tray_layout]]
        layout = [
            [sg.Column([[sg.Column(block_wheel, size=(460, 400), pad=self.BPAD_LEFT_INSIDE)]],
                       pad=self.BPAD_LEFT, background_color=self.BORDER_COLOR),
             sg.Column(block_tray, size=(460, 400), pad=self.BPAD_RIGHT, element_justification='center')]]

        self.window = sg.Window('Roller Bench UI', layout, margins=(3, 3), background_color=self.BORDER_COLOR)

    def calculate_the_ratio(self):
        self.event_server = HostEventsClient(server_type='raw_input')

        self.Faulhaber.set_torque((-360))

        # velocity in rpm/m (rotation per minute)
        # self.MaxonEpos2.set_velocity(velocity=100)  # set velocity mode
        self.MaxonEpos2.set_position_mode(velocity=10)
        # set speed ya da set velocity kullanacaksin

        self.event_server.start_events_capture()
        sleep(2)

        self.MaxonEpos2.set_position(-360)
        sleep(2)
        # self.MaxonEpos2.set_velocity(velocity=100)  # set velocity mode

        mouse_events, _, _ = self.event_server.stop_events_capture()

        last_two_wheel_counts = []
        for event in reversed(mouse_events):
            if event.type == "wheel_down":
                last_two_wheel_counts.append(event)
            elif event.type == "wheel_up":
                last_two_wheel_counts.append(event)

        delta = last_two_wheel_counts[3].monotonic - last_two_wheel_counts[4].monotonic
        delta /= 10 ** 6
        angle_degree = (60) * delta
        result_ratio = 15 / angle_degree

        # mouse_movement = self.MaxonEpos2.move_wheel_with_mouse(360)
        wheel_ratio = 1 / result_ratio

        return wheel_ratio

    def calculate_mouse_ratchet(self, raw_ratio):
        # event_server = HostEventsClient(server_type='raw_input')
        # wheel_ratio = 1 / raw_ratio
        self.MaxonEpos2.set_ratio(raw_ratio)

        # start recording ratchet
        self.event_server.start_events_capture()
        sleep(2)

        self.MaxonEpos2.set_position(360)
        sleep(2)

        mouse_events, _, _ = self.event_server.stop_events_capture()

        ratchet_counts = []
        for event in reversed(mouse_events):
            if event.type == "wheel_down":
                ratchet_counts.append(event)

        a = len(ratchet_counts) - 1
        # stop recording ratchet, ratchet nb should be equal to ~24

        return a

    def calculate_mouse_reverse_ratchet(self, raw_ratio):
        self.MaxonEpos2.set_ratio(raw_ratio)

        # start recording ratchet
        self.event_server.start_events_capture()
        sleep(2)

        self.MaxonEpos2.set_position(-360)
        sleep(2)

        mouse_events, _, _ = self.event_server.stop_events_capture()

        ratchet_counts_reverse = []
        for event in reversed(mouse_events):
            if event.type == "wheel_up":
                ratchet_counts_reverse.append(event)

        b = len(ratchet_counts_reverse) - 1
        # stop recording ratchet, ratchet nb should be equal to ~24

        return b

    # 360  °
    def set_angular_angle(self, values):
        """
            Set the angular angle based on the input values.
            :param values: A dictionary containing the input values.
            :return  angle : The angle that was set.

        """

        angular_angle = values['ANGULAR_POSITION'].split(' ')
        splitted_angular_angle = angular_angle[0]
        angle = int(splitted_angular_angle)
        self.MaxonEpos2.set_position(angle)
        return angle

    def calculate_d1_movement(self, angle, d1_diameter):
        """
             Calculate the movement distance of D1 based on the given angle and D1 diameter.

            :param angle:The angle in degrees.
            :param d1_diameter: The diameter of D1
            :return: The calculated movement distance of D1.
        """
        return angle * (d1_diameter / self.D2)

    def calculate_movement_time(self, angle, velocity):
        """
            Calculate the movement time based on the given angle and velocity.
            :param angle: The angle in degrees.
            :param velocity:The velocity of movement.
            :return: The calculated movement time in seconds.
        """
        angle_radian = angle / 57.296
        time = (angle_radian / velocity) * 10
        return time

    def event(self):
        """
            Runs UI application that listens for events and performs actions based on the event and values.
        """
        while True:
            event, values = self.window.read()

            if event == sg.WINDOW_CLOSED:
                break

            if event == 'START_WHEEL':
                angular_speed = values['ANGULAR_SPEED']
                velocity = int(angular_speed)
                self.MaxonEpos2.set_position_mode(velocity)

                angle = self.set_angular_angle(values)
                d1_diameter = values['D1_DIAMETER']
                d1_diameter_float = float(d1_diameter)
                d1_movement = self.calculate_d1_movement(angle, d1_diameter_float)
                self.window['D1_MOVEMENT'].update(value=d1_movement)

                time = self.calculate_movement_time(angle, velocity)
                formatted_time = "{:.2f}".format(time)
                self.window['timer_text'].update(value=formatted_time)

            elif values['ENABLE_DRIVE']:
                self.Faulhaber.switch_drive(enabled=True)
                if event == 'TRAY_PRESSURE':
                    press_value = values['TRAY_PRESSURE']
                    press_val = int(press_value)
                    self.Faulhaber.set_torque(press_val)
                elif event == 'TRAY_SLIDER':
                    tray_slider = values['TRAY_SLIDER']
                    tray_slider_int = int(tray_slider)
                    self.Faulhaber.set_torque(tray_slider_int)

                elif event == 'STOP_SLIDER':
                    self.Faulhaber.set_torque(torque=0)
                    self.window['TRAY_SLIDER'].update(value=0)

            elif not values['ENABLE_DRIVE']:
                self.Faulhaber.switch_drive(enabled=False)
                self.Faulhaber.set_torque(torque=0)
                self.window['TRAY_SLIDER'].update(value=0)

        self.Faulhaber.switch_drive(enabled=False)
        self.Faulhaber.close_client()
        self.window.close()


roller_ui = Roller(usb_port=1, D2=50)
roller_ui.roller_layout()
ratio = roller_ui.calculate_the_ratio()
ratchet_number = roller_ui.calculate_mouse_ratchet(ratio)
reverse_ratchet_number = roller_ui.calculate_mouse_reverse_ratchet(ratio)
roller_ui.event()
