from time import sleep
import pytest
from python_pqa_libs.pypqa.services.host_events_client import HostEventsClient
from python_pqa_libs.pypqa.services.motor_controller import MaxonEpos2, FaulhaberMcV3
from pathlib import Path
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

# TODO check ratchet count one way in the test, then the other 2 turn (more than 1s pose between direction)

ratchet_count = 24
angle_ratchet = int(360 / ratchet_count) 


@pytest.fixture(scope="session")
def init_bench():
    """
    Base fixture
    """
    event_server = HostEventsClient(server_type='raw_input')

    wheel_ctr = MaxonEpos2()
    wheel_ctr.set_position_mode()

    press_ctr = FaulhaberMcV3(usb_port=1)
    press_ctr.set_mode(FaulhaberMcV3.OperationMode.TORQUE)
    press_ctr.switch_drive(enabled=True)

    # Calculate the ratio
    ratio = calculate_the_ratio(wheel_ctr, press_ctr, event_server)
    wheel_ctr.set_ratio(ratio)
    # apply it

    yield wheel_ctr, press_ctr, event_server

    press_ctr.switch_drive(enabled=False)
    press_ctr.close_client()


def wheel_counter(mouse_events):
    """
    Count wheel events in a list of mouse events.
    """
    wheel_counts = []
    wheel_counts_reverse = []
    for event in reversed(mouse_events):
        if event.type == "wheel_down":
            wheel_counts.append(event)
        elif event.type == "wheel_up":
            wheel_counts_reverse.append(event)

    return len(wheel_counts), wheel_counts, len(wheel_counts_reverse)


def calculate_the_ratio(wheel_ctr, press_ctr, event_server):
    """
    Calculate the ratio between system wheel and mice wheel.
    """
    press_ctr.set_torque((-360))
    wheel_ctr.set_position_mode(velocity=10)

    event_server.start_events_capture()
    sleep(2)

    wheel_ctr.set_position(360)
    sleep(2)

    mouse_events, _, _ = event_server.stop_events_capture()

    wheel_counts, wheel_events, wheel_counts_reverse = wheel_counter(mouse_events)

    delta = wheel_events[3].monotonic - wheel_events[4].monotonic
    delta /= 10 ** 6
    angle_degree = (60) * delta
    result_ratio = 15 / angle_degree

    wheel_ratio = 1 / result_ratio

    return wheel_ratio


def test_clockwise(init_bench):
    """
    Test the system behavior when the wheel rotates clockwise.
    """
    wheel_ctr, press_ctr, event_server = init_bench

    press_ctr.set_torque(-350)

    wheel_ctr.set_position_mode(velocity=10)

    event_server.start_events_capture()
    sleep(2)

    wheel_ctr.set_position(angle=360)
    sleep(2)

    mouse_events, _, _ = event_server.stop_events_capture()

    wheel_counts, _, _ = wheel_counter(mouse_events)

    assert 22 < wheel_counts < 27


def test_clockwise_reverse(init_bench):
    """
    Test the system behavior when the wheel rotates clockwise in reverse.
    """
    wheel_ctr, press_ctr, event_server = init_bench

    press_ctr.set_torque(-350)

    wheel_ctr.set_position_mode(velocity=10, acceleration=100, deceleration=100)

    event_server.start_events_capture()
    sleep(2)

    wheel_ctr.set_position(angle=-360)
    sleep(2)

    mouse_events, _, _ = event_server.stop_events_capture()

    _, _, wheel_counts_reverse = wheel_counter(mouse_events)

    assert 22 < wheel_counts_reverse < 27


@pytest.mark.parametrize("velocity", [90, 100, 130, 150])
def test_both_side_turning(init_bench, velocity):
    """
    Test the system with different wheel velocity for both  direction.
    """
    wheel_ctr, press_ctr, event_server = init_bench

    press_ctr.set_torque(-350)

    wheel_ctr.set_position_mode(velocity=velocity, acceleration=100, deceleration=100)

    event_server.start_events_capture()
    sleep(2)

    wheel_ctr.set_position(angle=360)
    sleep(2)

    wheel_ctr.set_position(angle=-360)
    sleep(2)

    mouse_events, _, _ = event_server.stop_events_capture()

    wheel_counts, wheel_events, wheel_counts_reverse = wheel_counter(mouse_events)

    assert 21 < wheel_counts < 27
    assert 21 < wheel_counts_reverse < 27
    assert wheel_counts == wheel_counts_reverse


@pytest.mark.parametrize("velocity", [50, 60, 70, 800])
def test_with_velocity(init_bench, velocity):
    """
    Test the system behavior with different wheel velocity settings.
    """
    wheel_ctr, press_ctr, event_server = init_bench

    press_ctr.set_torque(-350)

    wheel_ctr.set_position_mode(velocity=velocity, acceleration=300, deceleration=300)

    event_server.start_events_capture()
    sleep(2)

    wheel_ctr.set_position(angle=360)
    sleep(2)

    mouse_events, _, _ = event_server.stop_events_capture()

    wheel_counts, _, _ = wheel_counter(mouse_events)

    assert 20 < wheel_counts < 28


def quick_displacements_list_funtion():
    """
    Generate a list of test cases
    :return:list of tuple: A list of test cases, where each test case is represented as a tuple
                  (forward, backward, velocity)
    """
    repetition_values = [(3, 2), (4, 15), (10, 3), (7, 3), (4, 5), (9, 2)]
    velocity_list = [10, 20, 50, 100]
    test_cases = []
    for velocity in velocity_list:
        for forward, backward in repetition_values:
            test_cases.append((forward, backward, velocity))
    return test_cases


@pytest.mark.parametrize("forward, backward, velocity", quick_displacements_list_funtion())
def test_quick_displacements(init_bench, forward, backward, velocity):
    """
    Several ratchets at a time, but not too fast
    :param forward:direction of clockwise
    :param backward: direction of reverse the clockwise
    """
    wheel_ctr, press_ctr, event_server = init_bench

    wheel_ctr.set_position_mode(velocity=velocity, acceleration=100, deceleration=100)

    event_server.start_events_capture()
    sleep(1)

    wheel_ctr.set_position(angle=angle_ratchet * forward)
    sleep(0.2)
    wheel_ctr.set_position(angle=-angle_ratchet * backward)
    sleep(0.2)

    mouse_events, _, _ = event_server.stop_events_capture()
    wheel_counts, _, wheel_counts_reverse = wheel_counter(mouse_events)

    assert wheel_counts == forward
    assert wheel_counts_reverse == backward


@pytest.mark.parametrize("step", range(10))
def test_ratchets_by_ratchets(init_bench, step):
    """
    One ratchet at a time several change of direction
    :param init_bench:A fixture that initializes the testing environment, providing access
                    to wheel control, pressure control, and event capture components.
    :param step:when the mose move ratchets by ratchets
    """
    wheel_ctr, press_ctr, event_server = init_bench

    wheel_ctr.set_position_mode(velocity=50, acceleration=100, deceleration=100)

    event_server.start_events_capture()
    sleep(1)

    wheel_ctr.set_position(angle=angle_ratchet)
    sleep(0.2)

    wheel_ctr.set_position(angle=-angle_ratchet)
    sleep(0.2)

    mouse_events, _, _ = event_server.stop_events_capture()

    wheel_counts, _, wheel_counts_reverse = wheel_counter(mouse_events)

    assert wheel_counts == 1
    assert wheel_counts_reverse == 1
    assert wheel_counts == wheel_counts_reverse


@pytest.mark.parametrize("laps", range(2))
def test_very_slow_ratchets(init_bench, laps):
    """
    Move from one ratchet to the next one very slowly(3-5 seconds for 1 ratchet)
    :param laps:one full turn for mice
    """
    wheel_ctr, press_ctr, event_server = init_bench

    wheel_ctr.set_position_mode(velocity=5, acceleration=100, deceleration=100)

    event_server.start_events_capture()
    sleep(1)

    wheel_ctr.set_position(angle=360)

    mouse_events, _, _ = event_server.stop_events_capture()
    wheel_counts, _, _ = wheel_counter(mouse_events)

    assert 22 < wheel_counts < 26


@pytest.mark.parametrize("laps", range(2))
def test_ratchets_two_laps(init_bench, laps):
    """
    One ratchet at a time and least two laps
    :param laps:one full turn for mice
    """
    wheel_ctr, press_ctr, event_server = init_bench

    wheel_ctr.set_position_mode(velocity=2, acceleration=100,
                                deceleration=100)  # try with velocity with two or more 5 works,

    event_server.start_events_capture()
    sleep(1)

    wheel_ctr.set_position(angle=360)

    mouse_events, _, _ = event_server.stop_events_capture()
    wheel_counts, _, _ = wheel_counter(mouse_events)

    assert 22 < wheel_counts < 26
