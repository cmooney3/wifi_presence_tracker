#!/usr/bin/python

import BaseHTTPServer
import pickle
import time

from jinja2 import Template, Environment, FileSystemLoader

LOG_FILENAME="log.p"
TEMPLATE_FILENAME="chart.html"

ERROR_HTML="<html><head><title>ERROR</title></head><body><h1>ERROR</h2><p>{}</p></body></html>"
LOAD_LOG_ERROR_HTML=ERROR_HTML.format("Failed to load the data logs.")
EMPTY_LOG_ERROR_HTML=ERROR_HTML.format("The data logs appear empty. ({})")
TEMPLATE_ERROR_HTML=ERROR_HTML.format("Failed to load the html template. ({})")


HOST_NAME = '0.0.0.0'
PORT_NUMBER = 8000

def ConvertDate(date):
  return date.strftime("%Y-%m-%d %H:%M")

################################################################################
# Log parsing and HTML generation
################################################################################
def GeneratePageFromLog(log_filename):
  log_data = []
  try:
    with open(log_filename, 'rb') as log_file:
      while True:
        try:
          timestamp, present_devices = pickle.load(log_file)
          log_data.append({"timestamp": timestamp, "present_devices": list(present_devices)})
        except EOFError:
          if not log_data:
            return EMPTY_LOG_ERROR_HTML  
          else:
            break
  except Exception as exp:
    return LOAD_LOG_ERROR_HTML.format(exp)

  # Figure out a set of all the hostnames that are ever present
  full_hostname_set = set()
  for entry in log_data:
    full_hostname_set = full_hostname_set.union(entry["present_devices"])

  # Figure out the start/stop times of each spurt of being connected for each hostname
  events = {}
  for hostname in full_hostname_set:
    print hostname
    events[hostname] = [] 
    start_time = None
    for log in log_data:
      if start_time is None and hostname in log["present_devices"]:
        start_time = log["timestamp"] 
      elif start_time and hostname not in log["present_devices"]:
        events[hostname].append({"start": ConvertDate(start_time), "end": ConvertDate(log["timestamp"])})
        start_time = None
    if start_time:
      events[hostname].append({"start": ConvertDate(start_time), "end": ConvertDate(log_data[-1]["timestamp"])})
    for event in events[hostname]:
      print "\t" + event["start"] + " - " + event["end"]

  try:
    env = Environment(loader = FileSystemLoader(["."]))
    t = env.get_template(TEMPLATE_FILENAME)
  except Exception as exp:
    return TEMPLATE_ERROR_HTML.format(exp)
  
  return t.render(events=events)

################################################################################
# Server code here, handling HTTP requests
################################################################################
class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  def do_HEAD(s):
    s.send_response(200)
    s.send_header("Content-type", "text/html")
    s.end_headers()
  def do_GET(s):
    """Respond to a GET request."""
    page = GeneratePageFromLog(LOG_FILENAME)

    s.send_response(200)
    s.send_header("Content-type", "text/html")
    s.end_headers()
    s.wfile.write(page)

if __name__ == '__main__':
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)
