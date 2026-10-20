"""The last module of a discovery run (revision 9, 20 Oct 2026): the offline suite ran isolated. No test reached outside the loopback
interface (tests/_isolation.py records every attempt, even one a handler swallowed), and no credential or private configuration was
visible to it."""

import os
import unittest

from tests import _isolation


class SuiteIsolation(unittest.TestCase):
    def test_no_test_reached_outside_the_loopback_interface(self):
        self.assertEqual(_isolation.ATTEMPTS, [], "network attempts outside the loopback interface:\n" + "\n".join(_isolation.ATTEMPTS[:5]))

    def test_no_credential_or_private_configuration_is_visible(self):
        from attest.secrets import KNOWN, SecretError, config_value, load_secret
        present = [name for name in _isolation.PRIVATE_VARIABLES if os.environ.get(name)]
        self.assertEqual(present, [], f"private variables set during the suite: {present}")
        self.assertIsNone(config_value("CODEX_BASE_URL"), "the development gateway's URL must not be configured in the offline suite")
        for name in KNOWN:
            with self.assertRaises(SecretError):
                load_secret(name)

    def test_the_guard_refuses_outside_the_loopback_interface(self):
        import socket
        before = len(_isolation.ATTEMPTS)
        with self.assertRaises(_isolation.NetworkForbidden):
            socket.getaddrinfo("example.invalid", 443)
        for port in sorted(_isolation.PROXY_PORTS)[:1]:  # this machine's proxy, when one is configured, is refused too
            with self.assertRaises(_isolation.NetworkForbidden):
                socket.create_connection(("127.0.0.1", port), timeout=1)
        del _isolation.ATTEMPTS[before:]  # these deliberate attempts are the control, not a finding


if __name__ == "__main__":
    unittest.main()
