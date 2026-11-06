import json
import unittest
from unittest.mock import patch, MagicMock
import orchestrator as orch


class OrchestratorTests(unittest.TestCase):
    def test_rejects_unapproved_image_even_if_present(self):
        with patch.object(orch, "_docker") as docker:
            with self.assertRaises(orch.DockerError):
                orch.ensure_image("alpine")
            docker.assert_not_called()

    def test_rejects_foreign_container(self):
        with patch.object(orch, "_docker") as docker:
            with self.assertRaises(orch.DockerError):
                orch.stop("another-project-db")
            docker.assert_not_called()

    def test_stop_absent_is_idempotent(self):
        with patch.object(orch, "_docker", return_value="") as docker:
            orch.stop("lab-u1-c2-abcdef")
            self.assertEqual(docker.call_count, 1)

    def test_stop_does_not_hide_docker_failure(self):
        with patch.object(orch, "_docker", side_effect=orch.DockerError("offline")):
            with self.assertRaises(orch.DockerError):
                orch.stop("lab-u1-c2-abcdef")

    def test_status_only_owned_running_name(self):
        with patch.object(orch, "_docker", return_value="lab-u1-c2-abcdef"):
            self.assertTrue(orch.status("lab-u1-c2-abcdef"))
            self.assertFalse(orch.status("lab-u2-c2-abcdef"))

    def test_network_rejects_unsafe_configuration(self):
        with patch.object(orch, "_docker", side_effect=[orch.NETWORK, '[{"Options": {}}]']):
            with self.assertRaises(orch.DockerError):
                orch.ensure_network()

    def test_start_allocates_port_and_hides_flag_from_arguments(self):
        calls = []
        def docker(*args, **kwargs):
            calls.append((args, kwargs))
            return json.dumps({"5000/tcp": [{"HostIp": "127.0.0.1", "HostPort": "43210"}]}) if args[0] == "inspect" else "id"
        response = MagicMock()
        response.__enter__.return_value.status = 200
        with patch.object(orch, "ensure_network"), patch.object(orch, "ensure_image"), patch.object(orch, "_docker", side_effect=docker), patch.object(orch.urllib.request, "urlopen", return_value=response):
            self.assertEqual(orch.start("lab-u1-c2-abcdef", "cti-lab/web-01", 5000, "CTF{0123456789abcdef}"), 43210)
        args, kwargs = calls[0]
        self.assertEqual(args[-1], "cti-lab/web-01")
        self.assertNotIn("CTF{0123456789abcdef}", " ".join(args))
        self.assertEqual(kwargs["env"]["FLAG"], "CTF{0123456789abcdef}")
        self.assertIn("127.0.0.1::5000", args)
        self.assertIn("--read-only", args)

    def test_docker_error_does_not_expose_output(self):
        result = MagicMock(returncode=1, stderr="FLAG=secret", stdout="")
        with patch.object(orch.subprocess, "run", return_value=result):
            with self.assertRaises(orch.DockerError) as caught:
                orch._docker("run")
            self.assertNotIn("secret", str(caught.exception))



@unittest.skipUnless(__import__("os").environ.get("RUN_DOCKER_TESTS") == "1", "Docker real opcional: RUN_DOCKER_TESTS=1")
class DockerIntegrationTests(unittest.TestCase):
    def test_two_isolated_instances_and_cleanup(self):
        import secrets
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
            info = json.loads(orch._docker("inspect", first))[0]
            self.assertTrue(info["HostConfig"]["ReadonlyRootfs"])
            self.assertEqual(info["Config"]["User"], "10001:10001")
            self.assertEqual(info["HostConfig"]["Memory"], 128 * 1024 * 1024)
            self.assertIn("ALL", info["HostConfig"]["CapDrop"])
            self.assertFalse(any("docker.sock" in mount.get("Source", "") for mount in info["Mounts"]))
            orch.stop(first)
            self.assertFalse(orch.status(first))
            self.assertTrue(orch.status(second))
        finally:
            orch.stop(first)
            orch.stop(second)

if __name__ == "__main__":
    unittest.main()

