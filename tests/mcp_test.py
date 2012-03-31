import datetime
import shutil
import StringIO
import tempfile

from testify import TestCase, class_setup, class_teardown, setup, teardown
from testify import assert_raises, assert_equal, suite, run
from testify.utils import turtle

from tron.core import action, job
from tron import mcp, scheduler, event
from tests import testingutils
from tron.utils import timeutils


class TestStateHandler(TestCase):
    @class_setup
    def class_setup_time(self):
        timeutils.override_current_time(datetime.datetime.now())
        self.now = timeutils.current_time()

    @class_teardown
    def class_teardown_time(self):
        timeutils.override_current_time(None)

    @setup
    def setup_mcp(self):
        nodes = turtle.Turtle()
        self.test_dir = tempfile.mkdtemp()
        self.mcp = mcp.MasterControlProgram(self.test_dir, "config")
        self.state_handler = self.mcp.state_handler
        self.action = action.Action("Test Action", "doit", nodes)

        self.action.command = "Test command"
        self.action.queueing = True
        self.action.node = turtle.Turtle()
        self.job = job.Job("Test Job", self.action)
        self.job.output_path = self.test_dir

        self.job.node_pool = turtle.Turtle()
        self.job.scheduler = scheduler.IntervalScheduler(datetime.timedelta(seconds=5))
        self.action.job = self.job

    @teardown
    def teardown_mcp(self):
        shutil.rmtree(self.test_dir)
        event.EventManager.get_instance().clear()

    @suite('integration')
    def test_reschedule(self):
        def callNow(sleep, func, run):
            raise NotImplementedError(sleep)

        self.mcp.job_scheduler.next_runs(self.job)
        #callLate = reactor.callLater
        #reactor.callLater = callNow

        #try:
        #    self.state_handler._reschedule(run)
        #    assert False
        #except NotImplementedError as sleep:
        #    assert_equals(sleep, 0)
#
        #try:
        #    self.state_handler._reschedule(run)
        #    assert False
        #except NotImplementedError as sleep:
        #    assert_equals(sleep, 5)
#
        #reactor.callLater = callLate

    def test_store_data(self):
        pass

    def test_load_data(self):
        pass


class TestNoVersionState(TestCase):
    @setup
    def build_files(self):
        self.state_data = """
sample_job:
    disable_runs: []
    enable_runs: []
    enabled: true
    runs:
    -   end_time: null
        run_num: 68801
        run_time: &id001 2011-01-25 18:21:12.614273
        runs:
        -   command: do_stuff
            end_time: null
            id: batch_email_sender.68801.check
            run_time: *id001
            start_time: null
            state: 0
        start_time: null
"""
        self.data_file = StringIO.StringIO(self.state_data)

    @teardown
    def teardown_mcp(self):
        event.EventManager.get_instance().clear()

    def test(self):
        handler = mcp.StateHandler(turtle.Turtle(), "/tmp")
        assert_raises(mcp.UnsupportedVersionError, handler._load_data_file, self.data_file)

class FutureVersionTest(TestCase):
    @setup
    def build_files(self):
        self.state_data = """
version: [99, 0, 0]
jobs:
    sample_job:
        disable_runs: []
        enable_runs: []
        enabled: true
        runs:
        -   end_time: null
            run_num: 68801
            run_time: &id001 2011-01-25 18:21:12.614273
            runs:
            -   command: do_stuff
                end_time: null
                id: batch_email_sender.68801.check
                run_time: *id001
                start_time: null
                state: 0
            start_time: null
"""
        self.data_file = StringIO.StringIO(self.state_data)

    @teardown
    def teardown_mcp(self):
        event.EventManager.get_instance().clear()

    def test(self):
        handler = mcp.StateHandler(turtle.Turtle(), "/tmp")
        assert_raises(mcp.StateFileVersionError, handler._load_data_file, self.data_file)


class TestMasterControlProgram(TestCase):

    @setup
    def build_actions(self):
        self.nodes = turtle.Turtle()
        self.test_dir = tempfile.mkdtemp()
        self.action = action.Action("Test Action", "doit", self.nodes)
        self.job = job.Job("Test Job", self.action)
        self.job.output_path = self.test_dir
        self.mcp = mcp.MasterControlProgram(self.test_dir, "config")
        self.job.node_pool = testingutils.TestPool()

    @teardown
    def teardown_actions(self):
        shutil.rmtree(self.test_dir)
        event.EventManager.get_instance().clear()

    def test_schedule_next_run(self):
        act = action.Action("Test Action", "doit", self.nodes)
        jo = job.Job("Test Job", act)
        jo.output_path = self.test_dir
        jo.node_pool = testingutils.TestPool()
        jo.scheduler = scheduler.DailyScheduler()

        act.job = jo
        act.command = "Test command"
        act.node = turtle.Turtle()

        def call_now(time, func, next):
            next.start()
            next.action_runs[0].succeed()

        callLater = mcp.reactor.callLater
        mcp.reactor.callLater = call_now
        try:
            self.mcp.job_scheduler.schedule(jo)
        finally:
            mcp.reactor.callLater = callLater
        next = jo.runs[0]

        assert_equal(len(filter(lambda r:r.is_success, jo.runs)), 1)
        assert_equal(jo.topo_actions[0], next.action_runs[0].action)
        assert next.action_runs[0].is_success
        assert next.is_success



if __name__ == '__main__':
    run()
