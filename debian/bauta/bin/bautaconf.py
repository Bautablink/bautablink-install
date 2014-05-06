#!/usr/bin/python
import os
import glob
import subprocess
import distutils.core
import shutil
import time
import argparse
import sys
import signal
import lockfile
import logging
import RPi.GPIO as GPIO

sleep_time = 5
authpwfile = '/bauta/etc/usbconfpw'
pwfile_glob = '/media/*/bautaconf/usbconfpw'
common_files = {
	"wpa_supplicant.conf": "/etc/wpa_supplicant/wpa_supplicant.conf",
	"foo.txt": "/bauta/foo.txt"
}

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--daemon", action="store_true")
parser.add_argument("-p", "--pidfile")
parser.add_argument("-D", "--debug", action="store_true")
parser.add_argument("-l", "--logfile")
arguments = parser.parse_args()

RED_PIN=15
GREEN_PIN=14
BLUE_PIN=18

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(RED_PIN, GPIO.OUT)
GPIO.setup(GREEN_PIN, GPIO.OUT)
GPIO.setup(BLUE_PIN, GPIO.OUT)

def blink(color, delay):
	if color == "red": GPIO.output(RED_PIN, 1)
	elif color == "green": GPIO.output(GREEN_PIN, 1)
	elif color == "blue": GPIO.output(BLUE_PIN, 1)
	elif color == "yellow": 
		GPIO.output(RED_PIN, 1)
		GPIO.output(GREEN_PIN, 1)
	elif color == "purple":
		GPIO.output(RED_PIN, 1)
		GPIO.output(BLUE_PIN, 1)
	elif color == "cyan":
		GPIO.output(GREEN_PIN, 1)
		GPIO.output(BLUE_PIN, 1)
	elif color == "white":
		GPIO.output(RED_PIN, 1)
		GPIO.output(GREEN_PIN, 1)
		GPIO.output(BLUE_PIN, 1)
	time.sleep(delay)
	GPIO.output(RED_PIN, 0)
	GPIO.output(GREEN_PIN, 0)
	GPIO.output(BLUE_PIN, 0)

def configure_from_path(path, log):
	log.info("configure from " + path)
	configure_script = os.path.join(path, "pre_configure.sh")
	if os.path.isfile(configure_script):
		log.debug("running " + configure_script)
		try:
			subprocess.check_call(["/bin/bash", configure_script])
		except Exception, e:
			log.error(configure_script + " failed: %s", str(e))

	for filename in common_files.keys():
		file_path = os.path.join(path, filename)
		destination = common_files[filename]
		if os.path.isfile(file_path):
			log.debug("copying " + filename)
			try:
				shutil.copyfile(file_path, destination)
			except Exception, e:
				log.error("Failed to copy " + filename + ": %s", str(e))

	files_path = os.path.join(path, "files")
	if os.path.isdir(files_path):
		log.debug("copying files from " + files_path)
		try:
			distutils.dir_util.copy_tree(files_path, "/")
		except Exception, e:
			log.error("Failed to copy files: %s", str(e))

	configure_script = os.path.join(path, "post_configure.sh")
	if os.path.isfile(configure_script):
		log.debug("running " + configure_script)
		try:
			subprocess.check_call(["/bin/bash", configure_script])
		except Exception, e:
			log.error(configure_script + " failed: %s", str(e))

def passwordfile_matches(pwfile, log):
	if not os.path.isfile(authpwfile): 
		log.debug("no password file " + authpwfile)
		return True
	try:
		f = open(pwfile, 'r')
		password = f.readline()
		f.close()
		f = open(authpwfile)
		authpassword = f.readline()
		f.close()
		return password == authpassword
	except Exception, e:
		log.warning("Error checking password file " + pwfile + ": %s", str(e))
		return False


def run():
	blink("red", 0.2)
	blink("green", 0.2)
	blink("blue", 0.2)

	logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', filename=arguments.logfile)
	log = logging.getLogger()
	log.setLevel(logging.INFO)
	if arguments.debug:
		log.setLevel(logging.DEBUG)

	log.info("Starting")
	if arguments.pidfile:
		pidf = open(arguments.pidfile, "w")
		pidf.write(str(os.getpid()) + "\n")
		pidf.close()

	foundit = False
	while True:
		matches = glob.glob(pwfile_glob)
		if not foundit and len(matches) > 0:
			foundit = True
			pwfile = matches[0]
			if passwordfile_matches(pwfile, log):
				blink("cyan", 0.5)
				configure_from_path(os.path.dirname(pwfile), log)
				blink("green", 0.5)
			else:
				blink("red", 0.5)
				log.warning("invalid password in " + pwfile)
		elif foundit and len(matches) == 0:
			blink("blue", 0.5)
			foundit = False
			log.debug("gone now - rebooting")
			try:
				subprocess.check_call(["/sbin/reboot"])
			except Exception, e:
				log.error("reboot failed: %s", str(e))
		elif foundit:
			log.debug("still there")
		else:
			log.debug("not seeing it")
		time.sleep(sleep_time)

def terminate(sig, foo):
	if arguments.pidfile:
		os.remove(arguments.pidfile)
	print("Clean terminate")
	blink("red", 0.1)
	sys.exit(0)

if __name__ == "__main__":
	if arguments.daemon:
		import daemon
		daemon_context = daemon.DaemonContext(working_directory="/tmp", uid=os.getuid())
		daemon_context.signal_map = { signal.SIGTERM: terminate }
		if arguments.pidfile:
			daemon_context.pidfile = lockfile.FileLock(arguments.pidfile)
		if arguments.debug:
			daemon_context.stdout = sys.stdout
			daemon_context.stderr = sys.stderr
		with daemon_context:
			run()
	else:
		run()
