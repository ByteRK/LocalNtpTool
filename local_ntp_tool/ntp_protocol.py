from __future__ import annotations

import datetime as dt
import struct
from dataclasses import dataclass

from .constants import NTP_EPOCH, REFERENCE_ID


def datetime_to_ntp_timestamp(value: dt.datetime) -> int:
    utc_value = value.astimezone(dt.timezone.utc)
    delta = utc_value - NTP_EPOCH
    seconds = int(delta.total_seconds())
    fraction = int((delta.total_seconds() - seconds) * (1 << 32))
    return (seconds << 32) | (fraction & 0xFFFFFFFF)


def ntp_timestamp_to_datetime(value: int) -> dt.datetime:
    seconds = value >> 32
    fraction = value & 0xFFFFFFFF
    return NTP_EPOCH + dt.timedelta(seconds=seconds + fraction / (1 << 32))


@dataclass(slots=True)
class NtpRequest:
    version: int
    mode: int
    transmit_timestamp: int


@dataclass(slots=True)
class NtpResponseInfo:
    transmit_time_utc: dt.datetime
    receive_time_utc: dt.datetime
    reference_time_utc: dt.datetime


def parse_request(packet: bytes) -> NtpRequest:
    if len(packet) < 48:
        raise ValueError("NTP packet must be at least 48 bytes")
    first_byte = packet[0]
    version = (first_byte >> 3) & 0x07
    mode = first_byte & 0x07
    transmit_timestamp = struct.unpack("!Q", packet[40:48])[0]
    return NtpRequest(version=version or 4, mode=mode, transmit_timestamp=transmit_timestamp)


def build_response(
    request: NtpRequest,
    reference_time_utc: dt.datetime,
    receive_time_utc: dt.datetime,
    transmit_time_utc: dt.datetime,
) -> bytes:
    li = 0
    version = request.version or 4
    mode = 4
    first_byte = (li << 6) | (version << 3) | mode
    root_delay = 0
    root_dispersion = 0
    reference_timestamp = datetime_to_ntp_timestamp(reference_time_utc)
    receive_timestamp = datetime_to_ntp_timestamp(receive_time_utc)
    transmit_timestamp = datetime_to_ntp_timestamp(transmit_time_utc)

    return struct.pack(
        "!BBBbIIIQQQQ",
        first_byte,
        1,
        4,
        -20,
        root_delay,
        root_dispersion,
        int.from_bytes(REFERENCE_ID, "big"),
        reference_timestamp,
        request.transmit_timestamp,
        receive_timestamp,
        transmit_timestamp,
    )


def build_client_request(version: int = 4) -> bytes:
    first_byte = (0 << 6) | (version << 3) | 3
    transmit_timestamp = datetime_to_ntp_timestamp(dt.datetime.now(dt.timezone.utc))
    packet = bytearray(48)
    packet[0] = first_byte
    packet[40:48] = struct.pack("!Q", transmit_timestamp)
    return bytes(packet)


def parse_server_response(packet: bytes) -> NtpResponseInfo:
    if len(packet) < 48:
        raise ValueError("NTP packet must be at least 48 bytes")
    unpacked = struct.unpack("!BBBbIIIQQQQ", packet[:48])
    reference_timestamp = unpacked[7]
    receive_timestamp = unpacked[9]
    transmit_timestamp = unpacked[10]
    return NtpResponseInfo(
        transmit_time_utc=ntp_timestamp_to_datetime(transmit_timestamp),
        receive_time_utc=ntp_timestamp_to_datetime(receive_timestamp),
        reference_time_utc=ntp_timestamp_to_datetime(reference_timestamp),
    )
