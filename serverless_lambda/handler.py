import datetime
import json
import logging
import os
import re
import zlib
import boto3
import dateutil.parser
import psycopg2
from dynamodb_json import json_util as dynamo_json

logger = logging.getLogger()
logger.setLevel(logging.getLevelName(os.environ["LOG_LEVEL"]))

def insert_postgres(event, _context):
    pg = psycopg2.connect(
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASS"],
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"]
    )
    pg.set_session(autocommit=True)
    curs = pg.cursor()

    try:
        for record in s3_records(event):
            body = download_record(record)

            for mesh_event in body.split("\n"):
                logger.debug(mesh_event)
                if "proximity_event" in mesh_event:
                    pg_insert_proximity_event(curs, mesh_event)
                elif "dispense_event" in mesh_event:
                    pg_insert_dispense_event(curs, mesh_event)
                elif mesh_event == "":
                    continue
                else:
                    logger.warn("Unrecognized event: " + mesh_event)
    finally:
        logger.info("Closing connection")
        curs.close()
        pg.close()

def insert_dynamo(event, _context):
    dynamodb = boto3.client("dynamodb")

    for record in s3_records(event):
        body = download_record(record)

        for mesh_event in body.split("\n"):
            logger.debug(mesh_event)
            if "proximity_event" in mesh_event:
                dynamo_insert_proximity_event(dynamodb, mesh_event)
            elif "dispense_event" in mesh_event:
                dynamo_insert_dispense_event(dynamodb, mesh_event)
            elif mesh_event == "":
                continue
            else:
                logger.warn("Unrecognized event: " + mesh_event)

def s3_records(event):
    # Sns guarantees one record per payload:
    # https://aws.amazon.com/sns/faqs/#reliability
    return json.loads(event["Records"][0]["Sns"]["Message"])["Records"]

def download_record(record):
    S3 = boto3.resource("s3")
    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]
    contents = S3.Object(bucket, key).get()["Body"].read()
    if re.match(r"^.*\.gz$", key): # GZIP compressed
        # https://stackoverflow.com/a/2695575/1070025
        contents = zlib.decompress(contents, 16+zlib.MAX_WBITS)
    return contents.strip()

def dynamo_insert_proximity_event(dynamodb, proximity_event):
    attrs = json.loads(proximity_event).values()[0]

    item = {
        "badge_hwid": attrs["badge_hwid"],
        "captured_at-location_hub_hwid": "{}-{}".format(attrs["captured_at"], attrs["location_hub_hwid"]),
        "expire_at": expire_at(),
        "location_hub_hwid": attrs["location_hub_hwid"],
        "captured_at": attrs["captured_at"],
        "duration": attrs["duration"],
        "rssi_samples": attrs["rssi_samples"],
        "acc_samples": attrs["acc_samples"],
        "created_at": datetime.datetime.now().isoformat()
    }
    dynamodb.put_item(
        TableName=os.environ["PROXIMITY_EVENTS_DYNAMODB_TABLE"],
        Item=json.loads(dynamo_json.dumps(item))
    )

def dynamo_insert_dispense_event(dynamodb, dispense_event):
    attrs = json.loads(dispense_event).values()[0]

    item = {
        "badge_hwid": None,
        "captured_at-hygiene_sensor_hwid": "{}-{}".format(attrs["captured_at"], attrs["hygiene_sensor_hwid"]),
        "expire_at": expire_at(),
        "hygiene_sensor_hwid": attrs["hygiene_sensor_hwid"],
        "captured_at": attrs["captured_at"],
        "first_badge_hwid": attrs["first_badge_hwid"],
        "first_badge_rssi": attrs["first_badge_rssi"],
        "first_badge_acc": attrs["first_badge_acc"],
        "second_badge_hwid": possible_empty_string(attrs["second_badge_hwid"]),
        "second_badge_rssi": attrs["second_badge_rssi"],
        "second_badge_acc": attrs["second_badge_acc"],
        "third_badge_hwid": possible_empty_string(attrs["third_badge_hwid"]),
        "third_badge_rssi": attrs["third_badge_rssi"],
        "third_badge_acc": attrs["third_badge_acc"],
        "fourth_badge_hwid": possible_empty_string(attrs["fourth_badge_hwid"]),
        "fourth_badge_rssi": attrs["fourth_badge_rssi"],
        "fourth_badge_acc": attrs["fourth_badge_acc"],
        "created_at": datetime.datetime.now().isoformat()
    }

    for badge_hwid in [attrs["first_badge_hwid"], attrs["second_badge_hwid"], attrs["third_badge_hwid"], attrs["fourth_badge_hwid"]]:
        if not badge_hwid:
            break

        item["badge_hwid"] = badge_hwid

        dynamodb.put_item(
            TableName=os.environ["DISPENSE_EVENTS_DYNAMODB_TABLE"],
            Item=json.loads(dynamo_json.dumps(item))
        )

def expire_at():
    epoch = datetime.datetime.utcfromtimestamp(0)
    seconds = (
        datetime.datetime.now() +
        datetime.timedelta(days=int(os.environ["DYNAMO_EXPIRATION_DAYS"])) -
        epoch
    ).total_seconds()
    return int(seconds)

def possible_empty_string(string):
    return None if string == "" else string

def pg_insert_proximity_event(curs, proximity_event):
    attrs = json.loads(proximity_event).values()[0]
    curs.execute(
        '''
        INSERT INTO "proximity_events" ("captured_at", "badge_hwid",
        "location_hub_hwid", "duration", "rssi_samples", "acc_samples",
        "created_at") VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''',
        [
            dateutil.parser.parse(attrs["captured_at"]),
            attrs["badge_hwid"],
            attrs["location_hub_hwid"],
            attrs["duration"],
            attrs["rssi_samples"],
            attrs["acc_samples"],
            datetime.datetime.now()
        ]
    )

def pg_insert_dispense_event(curs, dispense_event):
    attrs = json.loads(dispense_event).values()[0]
    curs.execute(
        '''
        INSERT INTO "dispense_events" ("captured_at", "hygiene_sensor_hwid",
        "first_badge_hwid", "first_badge_rssi", "first_badge_acc",
        "second_badge_hwid", "second_badge_rssi", "second_badge_acc",
        "third_badge_hwid", "third_badge_rssi", "third_badge_acc",
        "fourth_badge_hwid", "fourth_badge_rssi", "fourth_badge_acc",
        "created_at") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s)
        ''',
        [
            dateutil.parser.parse(attrs["captured_at"]),
            attrs["hygiene_sensor_hwid"],
            attrs["first_badge_hwid"],
            attrs["first_badge_rssi"],
            attrs["first_badge_acc"],
            attrs["second_badge_hwid"],
            attrs["second_badge_rssi"],
            attrs["second_badge_acc"],
            attrs["third_badge_hwid"],
            attrs["third_badge_rssi"],
            attrs["third_badge_acc"],
            attrs["fourth_badge_hwid"],
            attrs["fourth_badge_rssi"],
            attrs["fourth_badge_acc"],
            datetime.datetime.now()
        ]
    )