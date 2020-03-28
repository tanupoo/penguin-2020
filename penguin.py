#!/usr/bin/env python

import sys
import os   # getenv() for extending PYTHONPATH.
import json
import logging
import asyncio
from aiohttp import web
import aiohttp
import logging
import ssl
from argparse import ArgumentParser
from datetime import datetime
from pymongo import MongoClient
import pymongo.errors
import uuid
from json2turtle import plod_json2turtle
from bson.objectid import ObjectId
import re

__CONF_SSL_CTX = "__ssl_ctx"
__CONF_DB_CONN = "__db_conn"

LOG_FMT = "%(asctime)s.%(msecs)d %(lineno)d %(message)s"
LOG_DATE_FMT = "%Y-%m-%dT%H:%M:%S"

ws_map = {}

#
# config
#
CONF_DEBUG_MODE = "debug_mode"
CONF_DEBUG_LEVEL = "debug_level"
CONF_LOG_FILE = "log_file"
CONF_SERVER_ADDR = "server_addr"
CONF_SERVER_PORT = "server_port"
CONF_SERVER_CERT = "server_cert"
CONF_TZ = "tz"
CONF_DB_ADDR = "db_addr"
CONF_DB_PORT = "db_port"
CONF_DB_NAME = "db_name"
CONF_DB_COLLECTION = "db_collction"
CONF_DB_USERNAME = "db_username"
CONF_DB_PASSWORD = "db_password"
CONF_DB_TIMEOUT = "db_timeout"
CONF_DB_MAX_ROWS = "db_max_rows"

def check_config(config, debug_mode=False):
    # overwrite the debug level if opt.debug is True.
    config.setdefault(CONF_DEBUG_MODE, debug_mode)
    config.setdefault(CONF_DEBUG_LEVEL, 0)
    config.setdefault(CONF_LOG_FILE, "penguin.log")
    # set the access point of the server.
    config.setdefault(CONF_SERVER_ADDR, "::")
    config.setdefault(CONF_SERVER_PORT, "65481")
    config.setdefault(CONF_TZ, "Asia/Tokyo")
    config.setdefault(CONF_SERVER_CERT, None)
    config.setdefault(CONF_DB_ADDR, "localhost")
    config.setdefault(CONF_DB_PORT, "27017")
    config.setdefault(CONF_DB_USERNAME, "root")
    config.setdefault(CONF_DB_PASSWORD, "example")
    config.setdefault(CONF_DB_NAME, "plod")
    config.setdefault(CONF_DB_COLLECTION, "draft")
    config.setdefault(CONF_DB_TIMEOUT, "2000")
    config.setdefault(CONF_DB_MAX_ROWS, "200")
    # convert into number.
    config[CONF_SERVER_PORT] = int(config[CONF_SERVER_PORT])
    config[CONF_DB_PORT] = int(config[CONF_DB_PORT])
    config[CONF_DB_TIMEOUT] = int(config[CONF_DB_TIMEOUT])
    config[CONF_DB_MAX_ROWS] = int(config[CONF_DB_MAX_ROWS])
    return True

#
# HTTP response
#
def common_access_log(request):
    """
    logger.info("Access from {} {} {}".format(request.remote,
                                              request.method,
                                              request.url))
    """
    pass

def dumps_utf8(data):
    return json.dumps(data, ensure_ascii=False)

def http_response_turtle(msg):
    return web.Response(body=msg, content_type="text/turtle")

def http_response(msg, status=200, log_text=None):
    res_msg = gen_common_response(msg, status=200, log_text=log_text)
    return web.json_response(res_msg, status=status, dumps=dumps_utf8)

def gen_common_response(msg, status=200, log_text=None):
    """
    msg: json object such string or dict.
    send below json string.
        {
            "msg_type": "response", # required.
            "status": status,       # required.
            "ts": "...",     # required.
            "result": msg           # required.
        }
    """
    if status != 200:
        logger.error("{} status={} error={}".format(msg, status, log_text))
    else:
        if config[CONF_DEBUG_LEVEL] > 1:
            logger.debug("result {} status={}".format(msg, status))
        else:
            logger.debug("result {} bytes status={}".format(len(msg), status))
    #
    return {
            "msg_type": "response",
            "status": status,
            "ts": datetime.now().isoformat(),
            "result": msg }

#
# MongoDB
#
class db_connector():
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.con = MongoClient(
                self.config[CONF_DB_ADDR],
                self.config[CONF_DB_PORT],
                username=self.config[CONF_DB_USERNAME],
                password=self.config[CONF_DB_PASSWORD],
                serverSelectionTimeoutMS=self.config[CONF_DB_TIMEOUT])
        self.db = self.con[self.config[CONF_DB_NAME]]
        self.col = self.db[self.config[CONF_DB_COLLECTION]]
        self.logger.info("Connect MongoDB {}.{} on {}:{}".
                         format(self.config[CONF_DB_NAME],
                                self.config[CONF_DB_COLLECTION],
                                self.config[CONF_DB_ADDR],
                                self.config[CONF_DB_PORT]))
        self.re_objectid = re.compile("^[a-f0-9]+$")
        self.re_eventid = re.compile("^[\-a-f0-9]+$")

    def db_submit(self, kv_data, **kwargs):
        try:
            self.col.insert_one(kv_data)
        except pymongo.errors.ServerSelectionTimeoutError as e:
            self.logger.error("timeout, mongodb looks not ready yet.")
            return False
        #
        self.logger.debug("Succeeded submitting data into MongoDB.")
        return True

    def find(self, selector):
        """
        selector: string like
            "5e7d9ace0810c91d43c60130" => { "_id": ObjectID("...") }
            "{}" => {}
            "1ef3c491-a892-4410-b4db-dc755c656cd1" => { "event_id": "..." }
            '{ "any_key": "any_value" }' => { "any_key": "any_value" }
            None => error
        """
        #
        if len(selector) == 0:
            selector = {}
        elif self.re_objectid.match(selector):
            selector = { "_id": ObjectId(selector) }
        elif self.re_eventid.match(selector):
            selector = { "event_id": selector }
        else:
            selector = json.loads(selector)
        #
        result = []
        try:
            nb_rows = 1
            for x in self.col.find(selector):
                _id = str(x.pop("_id"))
                x.update({"_id": f"{_id}"})
                result.append(x)
                nb_rows += 1
                if self.config[CONF_DB_MAX_ROWS] == 0:
                    continue
                elif nb_rows > self.config[CONF_DB_MAX_ROWS]:
                    break
            return True, result
        except pymongo.errors.ServerSelectionTimeoutError as e:
            return False, str(e)

#
# REST API
#
async def downlink_handler(request):
    common_access_log(request)
    if not request.can_read_body:
        return web.json_response({"result":"failed. no body"})
    #
    kx_data = await request.json()
    logger.debug("accepted downlink request: {}".format(kx_data))
    await send_downlink(kx_data)

async def provide_feeder_handler(request):
    """
    all document must be placed under the ui directory.
    """
    common_access_log(request)
    path = "./ui/feeder.html"
    logger.debug("DEBUG: serving {}".format(path))
    if os.path.exists(path):
        return web.FileResponse(path)
    else:
        raise web.HTTPNotFound()

async def get_doc_handler(request):
    """
    all document must be placed under the ui directory.
    """
    common_access_log(request)
    path = "./ui/{}".format(request.path)
    logger.debug("DEBUG: serving {}".format(path))
    if os.path.exists(path):
        return web.FileResponse(path)
    else:
        raise web.HTTPNotFound()

async def receive_feeder_handler(request):
    common_access_log(request)
    heaers = request.headers
    if config[CONF_DEBUG_LEVEL] > 1:
        logger.debug("---BEGIN OF REQUESTED HEADER---")
        for k,v in request.headers.items():
            logger.debug("{}: {}".format(k,v))
        logger.debug("---END OF REQUESTED HEADER---")
    # convert the content into JSON.
    content = await request.read()
    if config[CONF_DEBUG_LEVEL] > 1:
        logger.debug("---BEGIN OF REQUESTED DATA---")
        logger.debug(content)
        logger.debug("---END OF REQUESTED DATA---")
    try:
        if isinstance(content, bytes):
            kv_data = json.loads(content.decode("utf-8"))
        elif isinstance(content, str):
            kv_data = json.loads(content)
        else:
            return http_response(
                    "The payload type is neigther bytes nor str. {}"
                    .format(type(content)),
                    status=404)
    except json.decoder.JSONDecodeError as e:
        return http_response(
                "The payload format was not likely JSON.",
                status=404, log_text=str(e))

    # XXX
    # need to add some info such as event_id.
    event_id = str(uuid.uuid4())
    kv_data.update({"event_id": event_id})
    logger.debug("kv_data: {}".format(json.dumps(kv_data)))

    # submit kv_data into database if needed.
    if config[__CONF_DB_CONN]:
        logger.debug("db_submit() will be called.")
        if config[__CONF_DB_CONN].db_submit(kv_data):
            logger.info(f"Submited kv_data for {event_id} successfully.")
        ## if you use kv_data, you need to care aboout "_id":ObjectID().
        # if kv_data.get("_id"):
        #     kv_data.pop("_id")
    #
    return http_response({"event_id":event_id})

async def provide_plod_handler(request):
    """
    e.g. /tummy/json/all
    cond:
        all:
        event_id:
        _id:
        mongodb query:
    """
    if not config[__CONF_DB_CONN]:
        return False, "DB hasn't been ready."
    #
    output_format = request.match_info["fmt"]
    condition = request.match_info["cond"]
    if output_format not in ["json", "turtle"]:
        return False, f"{output_format} is not supported."
    # XXX should check the condition ?
    if condition == "all":
        condition = ""
    logger.debug(f"Try seraching db by [{condition}]")
    result = config[__CONF_DB_CONN].find(condition)
    if result[0] == False:
        return result
    if output_format == "json":
        return http_response(result[1])
    elif output_format == "turtle":
        return http_response_turtle(plod_json2turtle(result[1][0]))

def set_logger(log_file=None, logging_stdout=False,
               debug_mode=False):
    def get_logging_handler(channel, debug_mode):
        channel.setFormatter(logging.Formatter(fmt=LOG_FMT,
                                               datefmt=LOG_DATE_FMT))
        if debug_mode:
            channel.setLevel(logging.DEBUG)
        else:
            channel.setLevel(logging.INFO)
        return channel
    #
    # set logger.
    #   log_file: a file name for logging.
    logging.basicConfig()
    logger = logging.getLogger()
    if logging_stdout is True:
        logger.addHandler(get_logging_handler(logging.StreamHandler(),
                                              debug_mode))
    if log_file is not None:
        logger.addHandler(get_logging_handler(logging.FileHandler(log_file),
                                              debug_mode))
    if debug_mode:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    return logger

"""
main
"""
ap = ArgumentParser()
ap.add_argument("config_file", metavar="CONFIG_FILE",
                help="specify the config file.")
ap.add_argument("-d", action="store_true", dest="debug",
               help="enable debug mode.")
ap.add_argument("-D", action="store_true", dest="logging_stdout",
               help="enable to show messages onto stdout.")
opt = ap.parse_args()
# load the config file.
try:
    config = json.load(open(opt.config_file))
except Exception as e:
    print("ERROR: {} read error. {}".format(opt.config_file, e))
    exit(1)
if not check_config(config, debug_mode=opt.debug):
    print("ERROR: error in {}.".format(opt.config_file))
    exit(1)
# set logger.
logger = set_logger(log_file=config[CONF_LOG_FILE],
                    logging_stdout=opt.logging_stdout,
                    debug_mode=opt.debug)
# make ssl context.
logger.debug(f"cert specified: {config.get(CONF_SERVER_CERT)}")
if config.get(CONF_SERVER_CERT):
    config[__CONF_SSL_CTX] = ssl.create_default_context(
            ssl.Purpose.CLIENT_AUTH)
    config[__CONF_SSL_CTX].load_cert_chain(config[CONF_SERVER_CERT])
# make mongodb connection.
config[__CONF_DB_CONN] = db_connector(config, logger)
# make routes.
app = web.Application(logger=logger)
app.router.add_route("GET", "/crest", provide_feeder_handler)
app.router.add_route("POST", "/beak", receive_feeder_handler)
app.router.add_route("GET", "/tummy/{fmt:(json|turtle)}/{cond:.+}", provide_plod_handler)
app.router.add_route("GET", "/image/{name:.+\.png}", get_doc_handler)
app.router.add_route("GET", "/{name:.+\.(js|css|ico|map)}", get_doc_handler)
# /image/draft-penguin.png
logger.info("Starting Penguin, a PLOD server listening on {}://{}:{}/"
            .format("https" if config.get(CONF_SERVER_CERT) else "http",
                    config.get(CONF_SERVER_ADDR) if config.get(CONF_SERVER_ADDR) else "*",
                    config.get(CONF_SERVER_PORT)))
# start loop
loop = asyncio.get_event_loop()
loop.set_debug(opt.debug)
web_handler = app.make_handler()
server_coro = loop.create_server(web_handler,
                                 host=config.get(CONF_SERVER_ADDR),
                                 port=config.get(CONF_SERVER_PORT),
                                 ssl=config.get(__CONF_SSL_CTX))
event = loop.run_until_complete(server_coro)
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    loop.run_until_complete(web_handler.finish_connections(1.0))
    event.close()
    loop.run_until_complete(event.wait_closed())
    loop.run_until_complete(app.finish())
loop.close()
