import numpy as np

from schedule_risk.network import Link, project_duration


def test_serial_chain_adds_up():
    d = np.array([[3.0, 4.0, 5.0]])
    links = [Link(1, 2), Link(2, 3)]
    assert project_duration(d, [1, 2, 3], links)[0] == 12


def test_parallel_paths_take_the_longest():
    d = np.array([[2.0, 7.0, 3.0, 1.0]])
    links = [Link(1, 2), Link(1, 3), Link(2, 4), Link(3, 4)]
    assert project_duration(d, [1, 2, 3, 4], links)[0] == 10


def test_start_to_start_overlap():
    # successor starts halfway through a 10-day predecessor, at day 5
    d = np.array([[10.0, 8.0]])
    links = [Link(1, 2, "SS", 0.5)]
    assert project_duration(d, [1, 2], links)[0] == 13


def test_overlapped_activity_cannot_finish_first():
    d = np.array([[10.0, 2.0]])
    links = [Link(1, 2, "SS", 0.5)]
    assert project_duration(d, [1, 2], links)[0] == 10


def test_every_iteration_is_scheduled_separately():
    d = np.array([[1.0, 1.0], [5.0, 2.0]])
    links = [Link(1, 2)]
    assert list(project_duration(d, [1, 2], links)) == [2.0, 7.0]
