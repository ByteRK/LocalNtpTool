from __future__ import annotations

import datetime as dt
import unittest

from local_ntp_tool.ntp_protocol import (
    build_client_request,
    build_response,
    parse_request,
    parse_server_response,
)


class NtpProtocolTests(unittest.TestCase):
    def test_round_trip_request_response(self) -> None:
        request_packet = build_client_request()
        request = parse_request(request_packet)
        now = dt.datetime(2026, 6, 15, 12, 0, 0, tzinfo=dt.timezone.utc)
        response_packet = build_response(request, now, now, now)
        response = parse_server_response(response_packet)
        self.assertEqual(response.transmit_time_utc, now)
        self.assertEqual(response.receive_time_utc, now)
        self.assertEqual(response.reference_time_utc, now)


if __name__ == "__main__":
    unittest.main()
