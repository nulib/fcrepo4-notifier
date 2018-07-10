#!/usr/bin/env python

import boto3
import os
import stomp
import sys
import time
import wait

from urllib.parse import urlparse

def connect_and_subscribe(conn, topic):
  conn.start()
  conn.connect()
  conn.subscribe(destination=topic, id=123, ack='auto')

class SnsListener(stomp.listener.ConnectionListener):
  def __init__(self, conn, topic, sns_topic):
    self.conn = conn
    self.topic = topic
    self.sns_client = boto3.client('sns')
    self.sns_topic = sns_topic

  def on_message(self, headers, body):
    identifier = headers.get('org.fcrepo.jms.identifier', '')
    if identifier != '':
      attributes = {}
      for key, value in headers.items():
        if value != '':
          attributes[key] = { 'DataType': 'String', 'StringValue': value }

      event_types = ','.join([urlparse(x).fragment for x in headers['org.fcrepo.jms.eventType'].split(',')])
      print('Publishing %s : %s to %s' % (event_types, identifier, self.sns_topic))
      self.sns_client.publish(
        TopicArn=self.sns_topic,
        Message=body,
        MessageAttributes=attributes
      )

  def on_connecting(self, host_and_port):
    print('Connecting to %s:%d' % host_and_port)

  def on_connected(self, headers, body):
    print('Connected')

  def on_disconnected(self):
    print('Disconnected – attempting recovery')
    connect_and_subscribe(self.conn, self.topic)

  def on_hearbeat(self):
    print('Heartbeat')

stomp_host    = os.environ.get('STOMP_HOST', 'localhost')
stomp_port    = int(os.environ.get('STOMP_PORT', 61613))
stomp_topic   = os.environ.get('STOMP_TOPIC')
stomp_timeout = int(os.environ.get('STOMP_TIMEOUT', 60))
sns_topic   = os.environ.get('SNS_TOPIC')

print('Waiting for %s:%d to open' % (stomp_host, stomp_port))
wait.tcp.open(stomp_port, host=stomp_host, timeout=stomp_timeout)

stomp_client = stomp.Connection([(stomp_host, stomp_port)])
stomp_client.set_listener('snsbridge', SnsListener(stomp_client, stomp_topic, sns_topic))
connect_and_subscribe(stomp_client, stomp_topic)

while stomp_client.transport.running:
  time.sleep(10)
