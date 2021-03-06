"""Tests the vsim backend."""

from unittest import TestCase, skipIf
import os
import tempfile
from plumbum import local
from .common import run_vhdeps, MockMissingImport

DIR = os.path.realpath(os.path.dirname(__file__))

def vsim_installed():
    """Returns whether vsim is installed."""
    try:
        from plumbum.cmd import vsim #pylint: disable=W0611,C0415
        return True
    except ImportError:
        return False

@skipIf(not vsim_installed(), 'missing vsim')
class TestVsimReal(TestCase):
    """Tests the vsim backend by actually invoking vsim and checking the test
    suite result."""

    def test_all_good(self):
        """Test running vsim on a single passing test case"""
        code, out, _ = run_vhdeps('vsim', '-i', DIR+'/simple/all-good')
        self.assertEqual(code, 0)
        self.assertTrue('working!' in out)
        self.assertTrue('PASSED  work.test_tc' in out)
        self.assertTrue('Test suite PASSED' in out)
        self.assertFalse('modelsim.ini' in os.listdir(DIR+'/simple/all-good'))
        self.assertFalse('vsim.wlf' in os.listdir(DIR+'/simple/all-good'))

    def test_multiple_per_file(self):
        """Test running vsim on a file with multiple test cases"""
        code, out, _ = run_vhdeps('vsim', '-i', DIR+'/complex/multi-tc-per-file')
        self.assertEqual(code, 0)
        self.assertTrue('working!' in out)
        self.assertTrue('PASSED  work.foo_tc' in out)
        self.assertTrue('PASSED  work.bar_tc' in out)
        self.assertTrue('Test suite PASSED' in out)
        self.assertFalse('modelsim.ini' in os.listdir(DIR+'/complex/multi-tc-per-file'))
        self.assertFalse('vsim.wlf' in os.listdir(DIR+'/complex/multi-tc-per-file'))

    def test_failure(self):
        """Test running vsim on a single failing test case"""
        code, out, _ = run_vhdeps('vsim', '-i', DIR+'/simple/failure')
        self.assertNotEqual(code, 0)
        self.assertTrue('uh oh!' in out)
        self.assertTrue('FAILED  work.test_tc' in out)
        self.assertTrue('Test suite FAILED' in out)
        self.assertFalse('modelsim.ini' in os.listdir(DIR+'/simple/failure'))
        self.assertFalse('vsim.wlf' in os.listdir(DIR+'/simple/failure'))

    def test_timeout(self):
        """Test running vsim on a single test case that times out"""
        code, out, _ = run_vhdeps('vsim', '-i', DIR+'/simple/timeout')
        self.assertNotEqual(code, 0)
        self.assertTrue('TIMEOUT work.test_tc' in out)
        self.assertTrue('Test suite FAILED' in out)
        self.assertFalse('modelsim.ini' in os.listdir(DIR+'/simple/timeout'))
        self.assertFalse('vsim.wlf' in os.listdir(DIR+'/simple/timeout'))

    def test_infinite(self):
        """Test running vsim on a single test case that does not terminate"""
        code, out, _ = run_vhdeps('vsim', '-i', DIR+'/simple/infinite')
        self.assertNotEqual(code, 0)
        self.assertTrue('TIMEOUT work.test_tc' in out)
        self.assertTrue('Test suite FAILED' in out)
        self.assertFalse('modelsim.ini' in os.listdir(DIR+'/simple/infinite'))
        self.assertFalse('vsim.wlf' in os.listdir(DIR+'/simple/infinite'))

    def test_error(self):
        """Test running vsim on a single test case that fails to
        elaborate"""
        code, _, _ = run_vhdeps('vsim', '-i', DIR+'/simple/elab-error')
        self.assertNotEqual(code, 0)
        self.assertFalse('modelsim.ini' in os.listdir(DIR+'/simple/elab-error'))
        self.assertFalse('vsim.wlf' in os.listdir(DIR+'/simple/elab-error'))

    def parse_error(self):
        """Test running vsim on a single test case that fails to compile"""
        code, _, _ = run_vhdeps('vsim', '-i', DIR+'/simple/parse-error')
        self.assertNotEqual(code, 0)
        self.assertFalse('modelsim.ini' in os.listdir(DIR+'/simple/parse-error'))
        self.assertFalse('vsim.wlf' in os.listdir(DIR+'/simple/parse-error'))

    def test_default_timeout_success(self):
        """Test running vsim on a single test case that does not have a
        timeout specified, but succeeds within 1 ms"""
        code, out, _ = run_vhdeps('vsim', '-i', DIR+'/simple/default-timeout-success')
        self.assertEqual(code, 0)
        self.assertTrue('PASSED  work.test_tc' in out)
        self.assertTrue('Test suite PASSED' in out)
        self.assertFalse('modelsim.ini' in os.listdir(DIR+'/simple/default-timeout-success'))
        self.assertFalse('vsim.wlf' in os.listdir(DIR+'/simple/default-timeout-success'))

    def test_default_timeout_too_short(self):
        """Test running vsim on a single test case that does not have a
        timeout specified and takes longer than that to complete"""
        code, out, _ = run_vhdeps('vsim', '-i', DIR+'/simple/default-timeout-too-short')
        self.assertNotEqual(code, 0)
        self.assertTrue('TIMEOUT work.test_tc' in out)
        self.assertTrue('Test suite FAILED' in out)
        self.assertFalse('modelsim.ini' in os.listdir(DIR+'/simple/default-timeout-too-short'))
        self.assertFalse('vsim.wlf' in os.listdir(DIR+'/simple/default-timeout-too-short'))

    def test_multiple_ok(self):
        """Test running vsim on a test suite with multiple test cases that all
        succeed"""
        code, out, _ = run_vhdeps('vsim', '-i', DIR+'/simple/multiple-ok')
        self.assertEqual(code, 0)
        self.assertTrue('working!' in out)
        self.assertTrue('PASSED  work.foo_tc' in out)
        self.assertTrue('PASSED  work.bar_tc' in out)
        self.assertTrue('Test suite PASSED' in out)
        self.assertFalse('modelsim.ini' in os.listdir(DIR+'/simple/multiple-ok'))
        self.assertFalse('vsim.wlf' in os.listdir(DIR+'/simple/multiple-ok'))

    def test_partial_failure(self):
        """Test running vsim on a test suite with multiple test cases of which
        one fails"""
        code, out, _ = run_vhdeps('vsim', '-i', DIR+'/simple/partial-failure')
        self.assertEqual(code, 1)
        self.assertTrue('working!' in out)
        self.assertTrue('uh oh!' in out)
        self.assertTrue('FAILED  work.fail_tc' in out)
        self.assertTrue('PASSED  work.pass_tc' in out)
        self.assertTrue('Test suite FAILED' in out)
        self.assertFalse('modelsim.ini' in os.listdir(DIR+'/simple/partial-failure'))
        self.assertFalse('vsim.wlf' in os.listdir(DIR+'/simple/partial-failure'))

    def test_workdir(self):
        """Test the workdir for the test case for GHDL"""
        with tempfile.TemporaryDirectory() as tempdir:
            local['cp'](DIR+'/complex/file-io/test_tc.vhd', tempdir)
            with local.cwd(tempdir):
                code, _, _ = run_vhdeps('vsim')
            self.assertEqual(code, 0)
            self.assertEqual(sorted(os.listdir(tempdir)), ['output_file.txt', 'test_tc.vhd'])


class TestVsimMocked(TestCase):
    """Tests the vsim backend without calling a real vsim."""

    def test_tcl_single(self):
        """Test TCL output for a single test case to stdout"""
        code, out, _ = run_vhdeps('vsim', '--tcl', '-i', DIR+'/simple/all-good')
        self.assertEqual(code, 0)
        self.assertTrue('add_source {' + DIR + '/simple/all-good/test_tc.vhd} '
                        '{work} {-quiet -2008}' in out)
        self.assertTrue('add_test {work} {test_tc} {' + DIR + '/simple/all-good}' in out)

    def test_tcl_multi(self):
        """Test TCL output for a test suite to stdout"""
        code, out, _ = run_vhdeps('vsim', '--tcl', '-i', DIR+'/simple/multi-version')
        self.assertEqual(code, 0)
        self.assertTrue('add_source {' + DIR + '/simple/multi-version/bar_tc.08.vhd} '
                        '{work} {-quiet -2008}' in out)
        self.assertTrue('add_source {' + DIR + '/simple/multi-version/foo_tc.93.vhd} '
                        '{work} {-quiet -93}' in out)
        self.assertTrue('add_test {work} {bar_tc} {' + DIR + '/simple/multi-version}' in out)
        self.assertTrue('add_test {work} {foo_tc} {' + DIR + '/simple/multi-version}' in out)

    def test_tcl_versions(self):
        """Test TCL output for a test suite with mixed VHDL versions to
        stdout"""
        code, out, _ = run_vhdeps('vsim', '--tcl', '-i', DIR+'/vsim/supported-versions')
        self.assertEqual(code, 0)
        self.assertTrue('add_source {' + DIR + '/vsim/supported-versions/a.87.vhd} '
                        '{work} {-quiet -87}' in out)
        self.assertTrue('add_source {' + DIR + '/vsim/supported-versions/b.93.vhd} '
                        '{work} {-quiet -93}' in out)
        self.assertTrue('add_source {' + DIR + '/vsim/supported-versions/c.02.vhd} '
                        '{work} {-quiet -2002}' in out)
        self.assertTrue('add_source {' + DIR + '/vsim/supported-versions/test_tc.08.vhd} '
                        '{work} {-quiet -2008}' in out)
        self.assertTrue('add_test {work} {test_tc} {' + DIR + '/vsim/supported-versions}' in out)

    def test_tcl_vsim_flags(self):
        """Test vsim flags using -W and pragma"""
        code, out, _ = run_vhdeps(
            'vsim', '--tcl', '-i', DIR+'/vsim/flags',
            '-Ws,-foo,-bar', '-Ws,-baz')
        self.assertEqual(code, 0)
        self.assertTrue('{1 ms} {-a -b -c -novopt -foo -bar -baz}' in out)

    def test_tcl_vcom_flags(self):
        """Test vcom flags using -W and pragma"""
        code, out, _ = run_vhdeps(
            'vsim', '--tcl', '-i', DIR+'/vsim/flags',
            '-Wc,-foo,-bar')
        self.assertEqual(code, 0)
        self.assertTrue('add_source {' + DIR + '/vsim/flags/test_tc.vhd} '
                        '{work} {-quiet -2008 -d -e -foo -bar}' in out)

    def test_invalid_flags(self):
        """Test invalid flags for -W for vsim"""
        code, _, err = run_vhdeps(
            'vsim', '--tcl', '-i', DIR+'/simple/all-good',
            '-Wx,-foo,-bar')
        self.assertNotEqual(code, 0)
        self.assertTrue('invalid value for -W' in err)

        code, _, err = run_vhdeps(
            'vsim', '--tcl', '-i', DIR+'/simple/all-good',
            '-Ws')
        self.assertNotEqual(code, 0)
        self.assertTrue('invalid value for -W' in err)

    def test_tcl_vcom_pragmas(self):
        """Test vsim-specific pragmas"""
        code, out, _ = run_vhdeps(
            'vsim', '--tcl', '-i', DIR+'/vsim/pragma-1')
        self.assertEqual(code, 0)
        self.assertTrue('} True True {hello.do}' in out)

        code, out, _ = run_vhdeps(
            'vsim', '--tcl', '-i', DIR+'/vsim/pragma-2')
        self.assertEqual(code, 0)
        self.assertTrue('} False False {}' in out)

    def test_tcl_to_file(self):
        """Test TCL output to a file"""
        with tempfile.TemporaryDirectory() as tempdir:
            code, _, _ = run_vhdeps(
                'vsim', '--tcl',
                '-i', DIR+'/simple/all-good',
                '-o', tempdir + '/sim.do')
            self.assertEqual(code, 0)
            self.assertTrue(os.path.isfile(tempdir + '/sim.do'))

    def test_cleanup(self):
        """Test .cleanup file handling"""
        with local.env(PATH=DIR+'/vsim/fake-vsim:' + local.env['PATH']):
            with tempfile.TemporaryDirectory() as tempdir:
                with local.cwd(tempdir):
                    with open('.cleanup', 'w') as fil:
                        fil.write(tempdir + '/test1\n')
                        fil.write(tempdir + '/test2\n')
                    with open('test1', 'w') as fil:
                        pass
                    code, _, _ = run_vhdeps(
                        'vsim', '--no-tempdir',
                        '-i', DIR+'/simple/all-good')
                    self.assertEqual(code, 0)
                    self.assertEqual(sorted(os.listdir(tempdir)), ['vsim.do', 'vsim.log'])

    def test_unsupported_version(self):
        """Test unsupported VHDL versions"""
        code, _, err = run_vhdeps('vsim', '--tcl', '-i', DIR+'/vsim/unsupported-version')
        self.assertEqual(code, 1)
        self.assertTrue('VHDL version 2012 is not supported' in err)

    def test_no_vsim(self):
        """Test the error message that is generated when vsim is missing"""
        with local.env(PATH=''):
            code, _, err = run_vhdeps('vsim', '-i', DIR+'/simple/all-good')
            self.assertEqual(code, 1)
            self.assertTrue('no vsim-compatible simulator was found.' in err)

    def test_no_plumbum(self):
        """Test the error message that is generated when plumbum is missing"""
        with MockMissingImport('plumbum'):
            code, _, err = run_vhdeps('vsim', '-i', DIR+'/simple/all-good')
            self.assertEqual(code, 1)
            self.assertTrue('the vsim backend requires plumbum to be installed' in err)

    def test_gui_tempdir(self):
        """Test running (a fake) vsim in GUI mode in a temporary directory"""
        with local.env(PATH=DIR+'/vsim/fake-vsim:' + local.env['PATH']):
            with tempfile.TemporaryDirectory() as tempdir:
                with local.cwd(tempdir):
                    code, out, _ = run_vhdeps('vsim', '--gui', '-i', DIR+'/simple/all-good')
                    self.assertEqual(code, 0)
                    self.assertTrue('executing do file' in out)
                    self.assertFalse('vsim.do' in os.listdir(tempdir))
                    self.assertFalse('vsim.log' in os.listdir(tempdir))

    def test_gui_no_tempdir(self):
        """Test running (a fake) vsim in GUI mode in the working directory"""
        with local.env(PATH=DIR+'/vsim/fake-vsim:' + local.env['PATH']):
            with tempfile.TemporaryDirectory() as tempdir:
                with local.cwd(tempdir):
                    code, out, _ = run_vhdeps(
                        'vsim', '--gui', '--no-tempdir', '-i', DIR+'/simple/all-good')
                    self.assertEqual(code, 0)
                    self.assertTrue('executing do file' in out)
                    with open(tempdir + '/vsim.log', 'r') as log_fildes:
                        with open(tempdir + '/vsim.do', 'r') as do_fildes:
                            self.assertEqual(log_fildes.read(), do_fildes.read())

    def test_batch_no_tempdir(self):
        """Test running (a fake) vsim in batch mode in the working
        directory"""
        with local.env(PATH=DIR+'/vsim/fake-vsim:' + local.env['PATH']):
            with tempfile.TemporaryDirectory() as tempdir:
                with local.cwd(tempdir):
                    code, out, _ = run_vhdeps('vsim', '--no-tempdir', '-i', DIR+'/simple/all-good')
                    self.assertEqual(code, 0)
                    self.assertTrue('executing from stdin' in out)
                    with open(tempdir + '/vsim.log', 'r') as log_fildes:
                        self.assertTrue('add_test {work} {test_tc}' in log_fildes.read())
