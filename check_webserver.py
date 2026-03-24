#!/usr/bin/python3
import subprocess

def check_server():
    try:
     cmd = 'ps -A | grep httpd'
     subprocess.run(cmd, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
     print("success: web server is up and running")
    except subprocess.CalledProcessError:
     print("error: web server failed")

if __name__ == '__main__':
    check_server()
