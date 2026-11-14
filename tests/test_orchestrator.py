import os
import secrets
import unittest
from unittest.mock import patch, MagicMock
import orchestrator as orch

VMS = '"cti-lab-base" {11111111-1111-1111-1111-111111111111}\n"lab-u1-c2-abcdef" {22222222-2222-2222-2222-222222222222}'
FLAG = "CTF{0123456789abcdef}"


def fake_vbox(running="", owned=True, fail_on=None):
    calls = []

    def vbox(*args, **kwargs):
        calls.append(args)
        if fail_on and args[0] == fail_on:
            raise orch.LabError("falha")
        if args[:2] == ("list", "vms"):
            return VMS
        if args[:2] == ("list", "runningvms"):
            return running
        if args[0] == "getextradata":
            return "Value: 1" if owned else "No value set!"
        if args[0] == "snapshot":
            return 'SnapshotName="base"'
        return ""
    return vbox, calls


class OrchestratorTests(unittest.TestCase):
    def test_rejects_unapproved_image(self):
        with patch.object(orch, "_vbox") as vbox:
            with self.assertRaises(orch.LabError):
                orch.ensure_image("alpine")
            vbox.assert_not_called()

    def test_rejects_foreign_vm_name(self):
        with patch.object(orch, "_vbox") as vbox:
            with self.assertRaises(orch.LabError):
                orch.stop("another-project-vm")
            vbox.assert_not_called()

    def test_stop_absent_is_idempotent(self):
        vbox, calls = fake_vbox()
        with patch.object(orch, "_vbox", side_effect=vbox):
            orch.stop("lab-u9-c9-abcdef")
        self.assertFalse(any(c[0] in ("controlvm", "unregistervm") for c in calls))

    def test_stop_skips_vm_without_owner_marker(self):
        vbox, calls = fake_vbox(owned=False)
        with patch.object(orch, "_vbox", side_effect=vbox):
            orch.stop("lab-u1-c2-abcdef")
        self.assertFalse(any(c[0] == "unregistervm" for c in calls))

    def test_stop_powers_off_and_deletes(self):
        vbox, calls = fake_vbox(running='"lab-u1-c2-abcdef" {2222}')
        with patch.object(orch, "_vbox", side_effect=vbox):
            orch.stop("lab-u1-c2-abcdef")
        self.assertIn(("controlvm", "lab-u1-c2-abcdef", "poweroff"), calls)
        self.assertIn(("unregistervm", "lab-u1-c2-abcdef", "--delete"), calls)

    def test_stop_does_not_hide_failure(self):
        with patch.object(orch, "_vbox", side_effect=orch.LabError("offline")):
            with self.assertRaises(orch.LabError):
                orch.stop("lab-u1-c2-abcdef")

    def test_status_only_running_name(self):
        vbox, _ = fake_vbox(running='"lab-u1-c2-abcdef" {2222}')
        with patch.object(orch, "_vbox", side_effect=vbox):
            self.assertTrue(orch.status("lab-u1-c2-abcdef"))
            self.assertFalse(orch.status("lab-u2-c2-abcdef"))

    def test_missing_base_vm_is_reported(self):
        with patch.object(orch, "_vbox", return_value=""):
            with self.assertRaisesRegex(orch.LabError, "setup_virtualbox"):
                orch.ensure_base()

    def test_start_uses_linked_clone_local_port_and_hides_flag(self):
        vbox, calls = fake_vbox()
        response = MagicMock()
        response.__enter__.return_value.status = 200
        with patch.object(orch, "_vbox", side_effect=vbox), patch.object(orch, "_free_port", return_value=43210), \
                patch.object(orch.urllib.request, "urlopen", return_value=response):
            port = orch.start("lab-u1-c2-abcdef", "cti-lab/web-01", 5000, FLAG)
        self.assertEqual(port, 43210)
        clone = next(c for c in calls if c[0] == "clonevm")
        self.assertIn("link", clone)
        self.assertIn("lab,tcp,127.0.0.1,43210,,5000", [a for c in calls for a in c])
        flag_calls = [c for c in calls if FLAG in c]
        self.assertEqual(len(flag_calls), 1)
        self.assertEqual(flag_calls[0][:4], ("guestproperty", "set", "lab-u1-c2-abcdef", "/CTI/Flag"))
        self.assertIn("RDONLYGUEST", flag_calls[0])

    def test_readiness_timeout_cleans_up_instance(self):
        vbox, _ = fake_vbox()
        with patch.object(orch, "_vbox", side_effect=vbox), patch.object(orch, "_free_port", return_value=43210), \
                patch.object(orch.time, "monotonic", side_effect=[0, orch.READY_TIMEOUT + 1]), \
                patch.object(orch, "stop") as stop:
            with self.assertRaisesRegex(orch.LabError, "não ficou pronto"):
                orch.start("lab-u1-c2-abcdef", "cti-lab/web-01", 5000, FLAG)
            stop.assert_called_once_with("lab-u1-c2-abcdef")

    def test_failed_cleanup_preserves_original_start_error(self):
        vbox, _ = fake_vbox(fail_on="startvm")
        with patch.object(orch, "_vbox", side_effect=vbox), patch.object(orch, "_free_port", return_value=43210), \
                patch.object(orch, "stop", side_effect=orch.LabError("cleanup")):
            with self.assertRaises(orch.LabError) as caught:
                orch.start("lab-u1-c2-abcdef", "cti-lab/web-01", 5000, FLAG)
            self.assertTrue(caught.exception.__notes__)

    def test_rejects_invalid_flag_and_port(self):
        with patch.object(orch, "_vbox") as vbox:
            with self.assertRaises(orch.LabError):
                orch.start("lab-u1-c2-abcdef", "cti-lab/web-01", 5000, "flag; rm -rf /")
            with self.assertRaises(orch.LabError):
                orch.start("lab-u1-c2-abcdef", "cti-lab/web-01", 22, FLAG)
            vbox.assert_not_called()

    def test_os_execution_failure_is_safe_domain_error(self):
        with patch.object(orch.subprocess, "run", side_effect=PermissionError("secret host path")):
            with self.assertRaises(orch.LabError) as caught:
                orch._vbox("list", "vms")
            self.assertNotIn("secret", str(caught.exception))

    def test_error_does_not_expose_output(self):
        result = MagicMock(returncode=1, stderr="CTF{secret}", stdout="")
        with patch.object(orch.subprocess, "run", return_value=result):
            with self.assertRaises(orch.LabError) as caught:
                orch._vbox("guestproperty", "set")
            self.assertNotIn("secret", str(caught.exception))


@unittest.skipUnless(os.environ.get("RUN_VBOX_TESTS") == "1", "VirtualBox real opcional: RUN_VBOX_TESTS=1")
class VBoxIntegrationTests(unittest.TestCase):
    def test_two_isolated_instances_and_cleanup(self):
        first = "lab-u900001-c2-" + secrets.token_hex(3)
        second = "lab-u900002-c2-" + secrets.token_hex(3)
        flag1, flag2 = "CTF{" + secrets.token_hex(8) + "}", "CTF{" + secrets.token_hex(8) + "}"
        try:
            port1 = orch.start(first, "cti-lab/web-01", 5000, flag1)
            port2 = orch.start(second, "cti-lab/web-01", 5000, flag2)
            self.assertNotEqual(port1, port2)
            for port, flag in ((port1, flag1), (port2, flag2)):
                with orch.urllib.request.urlopen(f"http://127.0.0.1:{port}/backup-interno") as response:
                    self.assertEqual(response.read().decode(), "FLAG: " + flag)
            orch.stop(first)
            self.assertFalse(orch.status(first))
            self.assertTrue(orch.status(second))
        finally:
            orch.stop(first)
            orch.stop(second)


if __name__ == "__main__":
    unittest.main()
