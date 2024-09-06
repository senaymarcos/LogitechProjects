import os
import PySimpleGUI as sg
import csv
import datetime
from jinja2 import Environment
from mouse_functional_tester.report_templates.events_catcher import EventsListener
import threading
import time


class MseFunctional:
    layout = [[sg.Checkbox('mouse have the forward/back button', key='checking_specify', enable_events=True,
                           pad=(10, 10), expand_x=True)],

              [sg.HorizontalSeparator()],
              [sg.Text('ERROR LOG', text_color='black')],
              [sg.Multiline(autoscroll=True, size=(40, 10), key='multi', pad=(10, 10), expand_x=True)],
              [sg.HorizontalSeparator()],
              [sg.Text(f'User Action : ', key='MOUSE_TEXT', pad=(10, 10), expand_x=True)],
              [sg.HorizontalSeparator()],
              [sg.Button('Start test', pad=(10, 10), expand_x=True, key='START', button_color='black')]]

    def __init__(self):
        self.event_listener = EventsListener()
        self.window = sg.Window('Mouse Button Functionality ', MseFunctional.layout, size=(390, 380), resizable=True)
        self.error_str = ''
        self.test_results = []
        self.result_dict = {}

    def mouse_event(self):
        self.event_listener.events_queue.queue.clear()
        mouse_event = self.event_listener.events_queue.get()

        return mouse_event

    def listen_for_mouse_event(self):
        """
        Listens for two consecutive mouse events and calculates the time difference between them.
        Returns:
        tuple: A tuple containing the first mouse event, the second mouse event,
        and the time difference between the two events.
        """
        self.event_listener.events_queue.queue.clear()
        mouse_event_1 = self.event_listener.events_queue.get()
        start = time.time()
        mouse_event_2 = self.event_listener.events_queue.get()
        end = time.time()
        event_time_diff = float(end - start)

        return mouse_event_1, mouse_event_2, event_time_diff

    def check_state_event(self, event_to_check, mouse_event):
        """
        Checks if a given mouse event matches the expected event.
        """
        if mouse_event == f'{event_to_check}':
            self.error_str += f'{self.event_list[event_to_check]} : passed\n'
        else:
            self.error_str += f'{self.event_list[event_to_check]} : failed\n'

        self.result = self.error_str

    def test_runner_event_check(self, event_list):
        """
        Executes event checks for a given list of mouse events.
        """
        for event_to_check in event_list:
            self.window['START'].update(text='Start test')
            self.window['START'].update(disabled=True)
            self.window['MOUSE_TEXT'].update(value=f'User Action :  {event_list[event_to_check]} ')
            time.sleep(0.5)

            if event_to_check == 'wheel_up' or event_to_check == 'wheel_down':
                self.check_state_event(event_to_check, self.mouse_event())

                # elif event_to_check == 'wheel_down':
                # self.check_state_event(event_to_check, self.mouse_event())

            else:
                mouse_event_1, mouse_event_2, event_time_diff = self.listen_for_mouse_event()

                if mouse_event_1 == f'{event_to_check}_pressed' or mouse_event_2 == f'{event_to_check}_released':
                    self.error_str += f'{self.event_list[event_to_check]} : passed\n'

                else:
                    self.error_str += f'{event_list[event_to_check]} : failed\n'
                self.result = self.error_str

            self.colorize_text()
            self.window['START'].update(disabled=False)
        self.window['MOUSE_TEXT'].update(value=f'User Action : test finished ')
        self.window['START'].update(text='test finished')

        self.test_results.extend(self.result.split('\n'))
        self.test_results.pop()

    def convert_dict(self):
        """
        Converts a list of colon-separated key-value pairs into a dictionary.
        """
        for item in self.test_results:
            key, value = item.split(':')
            self.result_dict.update({key: value})

        return self.result_dict

    def colorize_text(self):
        """
        Colorizes and displays error messages in a tkinter window.
        """

        self.window['multi'].update(value='')
        lines = self.error_str.split('\n')
        for line in lines:
            if 'passed' in line:
                self.window['multi'].print(line, text_color='green')
            elif 'failed' in line:
                self.window['multi'].print(line, text_color='red')
            else:
                pass

            self.window['multi'].Widget.yview_moveto(1.0)

    def create_path(self):
        """
        Creates target directories and check the existence file path.
        """
        target_directory = 'Result_File'

        if not os.path.exists(target_directory):
            os.makedirs(target_directory)

        html_file = os.path.join(target_directory, f'result_{self.today()}_{self.time()}.html')
        csv_file = os.path.join(target_directory, f'result_{self.today()}_{self.time()}.csv')

        return csv_file, html_file

    def generate_csv(self):
        """Generate the CSV file report"""
        csv_file, _ = self.create_path()

        if os.path.exists(csv_file):
            print(f"{csv_file} file already exist.")
            return

        with open(csv_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Event', 'Result'])
            for event, result in self.convert_dict().items():
                writer.writerow([event, result])

        return csv_file

    def generate_html(self):
        """Generate the HTML report"""
        _, html_file = self.create_path()

        if os.path.exists(html_file):
            print(f"{html_file} file already exist.")
            return

        with open('mouse_functional_tester/report_templates/template.html', "r") as template:
            html_val = template.read()
            jinja_env = (
                Environment().from_string(html_val).render(test_name='test_report', test_data=self.convert_dict()))
            print(self.convert_dict())

        with open(html_file, "w") as html_report:
            html_report.write(jinja_env)

    @staticmethod
    def today():
        """Return the current date in the format"""
        dt = datetime.date.today()
        return f'{dt.year}_{dt.month}_{dt.day}'

    @staticmethod
    def time():
        """Return the current date in the format"""
        dt = datetime.datetime.now()
        return f'{dt.hour}_{dt.minute}_{dt.second}'

    def test_runner(self, checking_specify):
        """
        Executes a test suite for mouse events and generates HTML and CSV result files.
        """
        self.event_list = {'wheel_up': 'move up', 'wheel_down': 'move down',
                           'left': 'left click', 'right': 'right click',
                           'middle': 'middle button ',
                           'x1': 'back button', 'x2': 'forward button'
                           }

        self.event_list_without_back_forward_button = {'wheel_up': 'move up', 'wheel_down': 'move down',
                                                       'left': 'left click', 'right': 'right click',
                                                       'middle': 'middle button'}

        if checking_specify:
            self.test_runner_event_check(self.event_list)
        else:
            self.test_runner_event_check(self.event_list_without_back_forward_button)
        self.generate_html()
        self.generate_csv()

    def run(self):
        while True:
            event, values = self.window.read()
            check_specify = values['checking_specify']
            if event == sg.WIN_CLOSED or event == 'Cancel':
                break
            elif event == 'START':
                self.error_str = ''
                self.window['multi'].update(value='')
                threading.Thread(target=self.test_runner, args=(check_specify,)).start()
        self.window.close()
        self.event_listener.stop()


test_app = MseFunctional()
test_app.run()
