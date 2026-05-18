# SPDX-License-Identifier: AGPL-3.0-or-later
import socket
import time

from lib.wifi_client import connect_wifi

HOST = "192.168.8.103"
PORT = 61208


def test_tcp():
    print("Testing TCP connect to {}:{}".format(HOST, PORT))
    addr = socket.getaddrinfo(HOST, PORT)[0][-1]
    sock = socket.socket()
    sock.settimeout(5)
    try:
        sock.connect(addr)
        print("TCP OK")
    finally:
        sock.close()


def test_http_status():
    print("Testing HTTP /api/4/status")
    addr = socket.getaddrinfo(HOST, PORT)[0][-1]
    sock = socket.socket()
    sock.settimeout(8)
    try:
        sock.connect(addr)
        sock.send(b"GET /api/4/status HTTP/1.0\r\nHost: 192.168.8.103\r\nConnection: close\r\n\r\n")
        total = b""
        while True:
            chunk = sock.recv(256)
            if not chunk:
                break
            total += chunk
            if len(total) > 1024:
                break
        print(total)
    finally:
        sock.close()


connect_wifi()
time.sleep(1)
test_tcp()
test_http_status()
print("Diagnostic done")
