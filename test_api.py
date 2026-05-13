from flask import Flask
from rateLimiter import app
from time import sleep

fake_ips = ["192.168.6.9", "192.168.6.10", "192.168.6.11", "192.168.6.12"]

def client():
    app.config.update({'TESTING': True})
    with app.test_client() as client:
        for i in range(7):  # Attempt to access the endpoint more than MAX_RPM times
            response = client.get('/test')
            print(response.status_code, response.data.decode())
            if i <= 4:
                assert response.status_code == 200
            else:
                assert response.status_code == 429
        sleep(61)
        for i in range(5): # Access the endpoint with delays in between requests to test further
            response = client.get('/test')
            print(response.status_code, response.data.decode())
            sleep(20)
            assert response.status_code == 200
        for ip in fake_ips: # Access the endpoint with different IPs to test the rate limiter's IP-based functionality
            for i in range(6):
                response = client.get('/test', environ_base={'REMOTE_ADDR': ip})
                print(f"IP: {ip}, Status Code: {response.status_code}, Response: {response.data.decode()}")
                if i <= 4:
                    assert response.status_code == 200
                else:
                    assert response.status_code == 429

client()