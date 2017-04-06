#!/usr/bin/env python2.7
import socket, fcntl, struct, sys, subprocess, binascii, re, string, logging, time, os, commands, datetime, signal
import SocketServer
from daemon import Daemon
from threading import Lock

def ExecCmdWithTimeout(commands, timeout):
	start_time = datetime.datetime.now()
	process = subprocess.Popen(commands, stdout = subprocess.PIPE, stderr = subprocess.PIPE)

	while process.poll() is None:
		time.sleep(0.3)
		now = datetime.datetime.now()
		if (now - start_time).seconds > timeout:
			os.kill(process.pid, signal.SIGKILL)
			os.waitpid(-1, os.WNOHANG)
			return None

	return process.stdout.read()

class RequestHandler(SocketServer.BaseRequestHandler):
	def handle(self):
		socket = self.request[1]
		socket.settimeout(5)
		data = self.request[0] # string

		logging.info("client address: " + self.client_address[0])
		logging.info("request: " + data)
		
		output = ExecCmdWithTimeout(["/data/XXX.sh", data], 20)
		if None == output:
			output = "process run timeout"

		logging.info("output:\n" + output + "\n")

		socket.sendto(output, self.client_address)

class ServerDaemon(Daemon):
	def get_ip_address(self, ifname):
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		return socket.inet_ntoa(fcntl.ioctl(
			s.fileno(),
			0x8915, # SIOCGIFADDR
			struct.pack('256s', ifname[:15])
			)[20:24])

	def _run(self):
		HOST = self.get_ip_address("eth1")
		PORT = 8080
		
		server = SocketServer.UDPServer((HOST, PORT), RequestHandler)
		server.serve_forever()

if '__main__' == __name__:
	script_path = os.path.split(os.path.realpath(sys.argv[0]))[0]
	server_daemon = ServerDaemon(script_path + '/server_deamon.pid')
	if 2 == len(sys.argv):
		logging.basicConfig(filename = '/tmp/log/server_daemon.log', \
				level = logging.DEBUG, filemode = 'a', format = '%(asctime)s - %(levelname)s: %(message)s')
		if 'start' == sys.argv[1]:
			server_daemon.start()
		elif 'stop' == sys.argv[1]:
			server_daemon.stop()
		elif 'restart' == sys.argv[1]:
			server_daemon.restart()
		elif 'run' == sys.argv[1]: # not in daemon mode
			server_daemon._run()
		else:
			print "Unknown command"
			sys.exit(2)
		sys.exit(0)
	else:
		print "usage: %s start|stop|restart" % sys.argv[0]
		sys.exit(2)

