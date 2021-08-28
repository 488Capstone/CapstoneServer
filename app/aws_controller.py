import time
from settings import AWS_SECRET_ACCESS_KEY, AWS_ACCESS_KEY_ID
import boto3
import datetime
import json
import paho.mqtt.client as paho
import ssl

# DynamoDB controls using boto3 ###

# AWS files from env/settings
dynamo_client = boto3.client('dynamodb',
                             aws_access_key_id=AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                             region_name='us-east-1'
                             )


def get_items(device_id):
    """Gets all items from dynamo matching device number."""
    request = dynamo_client.query(
        ExpressionAttributeValues={
            ':v1': {'N': str(device_id)}},
        KeyConditionExpression='device_id = :v1', TableName='test'
    )
    items = request['Items']
    for item in items:
        try:
            item['temperature'] = item['device_data'].get('M').get('temperature').get('N')
        except:
            item['temperature'] = ' '
        item['moisture'] = item['device_data'].get('M').get('moisture').get('N')
        item['status'] = item['device_data'].get('M').get('status').get('N')
        try:
            item['battery'] = item['device_data'].get('M').get('battery').get('N')
        except:
            item['battery'] = ' '
        del item['device_data']
        del item['device_id']
        # item['device_id'] = item['device_id'].get('N')
        time_value = int(item['sample_time'].get('N')) / 1000
        item['sample_time'] = datetime.datetime.utcfromtimestamp(time_value).strftime('%Y-%m-%d %H:%M:%S:%f')

    return items

# AWS IOT controls using paho ###


# endpoint and cert/key settings.. paths with "/var" are remote
aws_host = "a20pl4sdwe06wd-ats.iot.us-east-1.amazonaws.com"
# ca_path = "/var/www/aws_flask/flask1/website/Thing_keys/root_ca.pem"
ca_path = "app/Thing_keys/root_ca.pem"
# cert_path = "/var/www/aws_flask/flask1/website/Thing_keys/certificate.pem.crt"
cert_path = "app/Thing_keys/certificate.pem.crt"
# key_path = "/var/www/aws_flask/flask1/website/Thing_keys/private.pem.key"
key_path = "app/Thing_keys/private.pem.key"
aws_port = 8883
client_id = "adfgadfg"

# setup paho client using settings
mqttc = paho.Client(client_id)
mqttc.tls_set(ca_path, certfile=cert_path, keyfile=key_path, cert_reqs=ssl.CERT_REQUIRED,
              tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)

# global client status
Connected = False
Subscribed = False
Msg_Received = False
Msg_payload = None


# aws response handlers
# connection success/fail
def on_connect(client, userdata, flags, rc):
    global Connected
    # print(f'rc: {rc}')
    if rc == 0:
        Connected = True
        print(f'CONNECTED client: {client}, userdata: {userdata}, flags: {flags}, rc: {rc}')
    else:
        Connected = False
        print(f'CONNECT BAD client: {client}, userdata: {userdata}, flags: {flags}, rc: {rc}')

def on_disconnect(client, userdata, rc):
    global Connected
    print(f'DISCONNECTED')
    mqttc.loop_stop()
    Connected = False

# message from subscribed topic (topic in msg.topic, shadow in msg.payload)
def on_message(client, userdata, msg):
    global Msg_Received, Msg_payload
    payload = json.loads(msg.payload)
    print(f'RECEIVED MESSAGE. Topic: {msg.topic}, payload: {payload}')
    Msg_Received = True
    Msg_payload = payload
    print(f'from aws, payload: {payload}')


def on_publish(client, userdata, mid):
    print(f'PUBLISH client: {client}, userdata: {userdata}, mid: {mid}')


def on_subscribe(client, userdata, mid, granted_qos):
    global Subscribed
    Subscribed = True
    print(f'SUBSCRIBED')


# bind handlers to client
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe
mqttc.on_disconnect = on_disconnect

def get_device_shadow(device_id):
    """Sends empty shadow get request to get entire shadow"""

    global Connected, Subscribed, Msg_Received, Msg_payload

    # update globals:
    Connected = False
    Subscribed = False
    Msg_Received = False
    Msg_payload = None

    thing_to_update = "Thing" + str(device_id)
    topic = "$aws/things/" + thing_to_update + "/shadow/get"  # must be double quotes
    payload = json.dumps("")

    print("CONNECTING")
    mqttc.connect(aws_host, aws_port, keepalive=10)

    while not Connected:
        print(f'waiting for connection')
        mqttc.loop()
        time.sleep(0.1)

    if Connected:
        # subscribe to topics, shadow will come on "accepted" topic, seen by on_message handler
        mqttc.subscribe(topic + "/accepted", 1)
        mqttc.subscribe(topic + "/rejected", 1)

    while Connected and not Subscribed:
        print(f'waiting for subscription')
        mqttc.loop()
        time.sleep(0.1)

    if Subscribed:
        mqttc.publish(topic, payload, qos=1)

    while Subscribed and not Msg_Received:
        print(f'waiting for message')
        mqttc.loop()
        time.sleep(0.1)

    if Msg_Received:
        print('msg received stopping loop')
        # unsubscribe to topics
        mqttc.unsubscribe(topic + "/accepted", 1)
        mqttc.unsubscribe(topic + "/rejected", 1)

    mqttc.disconnect()

    shadow = Msg_payload
    return shadow

def shadow_change_rqst(device_id, property_to_change, desired_state):
    """Request a change to device shadow."""
    thing_to_update = "Thing" + str(device_id)
    topic = "$aws/things/" + thing_to_update + "/shadow/update"  # must be double quotes
    payload = json.dumps({"state": {"desired": {property_to_change: desired_state}}})

    mqttc.connect(aws_host, aws_port, keepalive=10)
    mqttc.loop_start()
    mqttc.publish(topic, payload, qos=1)
    mqttc.loop_stop()
    mqttc.disconnect()


def update_zip(device_id, new_zip):
    """Send a new zip to device shadow change requester."""
    shadow_change_rqst(device_id, "zip", new_zip)

def update_water_start_stop(device_id, cmd):
    """Send desire to shadow to immediately start or stop watering."""
    if cmd == "start":
        watering_desire = "True"
    else:
        watering_desire = "False"
    shadow_change_rqst(device_id, "watering", watering_desire)
