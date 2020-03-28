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

CONF_SERVER_ADDR = "server_addr"
CONF_SERVER_PORT = "server_port"
CONF_SERVER_CERT = "server_cert"
CONF_DEBUG_LEVEL = "debug_level"
CONF_TZ = "tz"
CONF_DEFAULT_SERVER_PORT = "65481"
CONF_SSL_CTX = "__ssl_ctx"
CONF_DB_ADDR = "db_addr"
CONF_DB_PORT = "db_port"
CONF_DB_NAME = "db_name"
CONF_DB_COLLECTION = "db_collction"
CONF_DB_USERNAME = "db_username"
CONF_DB_PASSWORD = "db_password"
CONF_DB_TIMEOUT = "db_timeout"
CONF_DB_CONN = "__db_conn"

LOG_FMT = "%(asctime)s.%(msecs)d %(lineno)d %(message)s"
LOG_DATE_FMT = "%Y-%m-%dT%H:%M:%S"

ws_map = {}

def common_access_log(request):
    """
    logger.info("Access from {} {} {}".format(request.remote,
                                              request.method,
                                              request.url))
    """
    pass

def gen_http_response(msg, status=200, log_text=None):
    res_msg = gen_common_response(msg, status=200, log_text=log_text)
    return web.json_response(res_msg, status=status)

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
        logger.debug("{} status={}".format(msg, status))
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
        self.debug_level = config.setdefault(CONF_DEBUG_LEVEL, 0)
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

    def db_submit(self, kv_data, **kwargs):
        try:
            self.col.insert_one(kv_data)
        except pymongo.errors.ServerSelectionTimeoutError as e:
            self.logger.error("timeout, mongodb looks not ready yet.")
            return False
        #
        self.logger.debug("Succeeded submitting data into MongoDB.")
        return True


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
            return gen_http_response(
                    "The payload type is neigther bytes nor str. {}"
                    .format(type(content)),
                    status=404)
    except json.decoder.JSONDecodeError as e:
        return gen_http_response(
                "The payload format was not likely JSON.",
                status=404, log_text=str(e))

    # XXX
    # need to add some info such as event_id.
    event_id = str(uuid.uuid4())
    kv_data.update({"event_id": event_id})
    logger.debug("kv_data: {}".format(json.dumps(kv_data)))

    # submit kv_data into database if needed.
    if config[CONF_DB_CONN]:
        logger.debug("db_submit() will be called.")
        if config[CONF_DB_CONN].db_submit(kv_data):
            logger.info(f"Submited kv_data for {event_id} successfully.")
        ## if you use kv_data, you need to care aboout "_id":ObjectID().
        # if kv_data.get("_id"):
        #     kv_data.pop("_id")
    #
    return gen_http_response({"status":"success", "event_id":event_id})

async def provide_json_handler(request):
    pass

async def provide_rdf_handler(request):
    pass

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

def check_config(config, debug_mode=False):
    # overwrite the debug level if opt.debug is True.
    if debug_mode == True:
        config[CONF_DEBUG_LEVEL] = 99
    logger.debug(f"expanded sys.path={sys.path}")
    # set the access point of the server.
    config.setdefault(CONF_SERVER_ADDR, "::")
    config.setdefault(CONF_SERVER_PORT, CONF_DEFAULT_SERVER_PORT)
    config[CONF_SERVER_PORT] = int(config[CONF_SERVER_PORT])
    config.setdefault(CONF_TZ, "Asia/Tokyo")
    config.setdefault(CONF_SERVER_CERT, None)
    config.setdefault(CONF_DB_ADDR, "localhost")
    config.setdefault(CONF_DB_PORT, "27017")
    config.setdefault(CONF_DB_USERNAME, "root")
    config.setdefault(CONF_DB_PASSWORD, "example")
    config.setdefault(CONF_DB_NAME, "plod")
    config.setdefault(CONF_DB_COLLECTION, "draft")
    config.setdefault(CONF_DB_TIMEOUT, "2000")
    config[CONF_DB_PORT] = int(config[CONF_DB_PORT])
    config[CONF_DB_TIMEOUT] = int(config[CONF_DB_TIMEOUT])
    # make ssl context.
    logger.debug(f"cert specified: {config.get(CONF_SERVER_CERT)}")
    if config.get(CONF_SERVER_CERT):
        config[CONF_SSL_CTX] = ssl.create_default_context(
                ssl.Purpose.CLIENT_AUTH)
        config[CONF_SSL_CTX].load_cert_chain(config[CONF_SERVER_CERT])
    #
    config[CONF_DB_CONN] = db_connector(config, logger)
    return True

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
# XXX
# XXX for test
# XXX
# load the config file.
try:
    config = json.load(open(opt.config_file))
except Exception as e:
    print("ERROR: {} read error. {}".format(opt.config_file, e))
    exit(1)
# update config.
config.setdefault(CONF_DEBUG_LEVEL, 0)  # only CONF_DEBUG_LEVEL needs here.
logger = set_logger(log_file=config.get("log_file"),
                    logging_stdout=opt.logging_stdout,
                    debug_mode=opt.debug)
if not check_config(config, debug_mode=opt.debug):
    print("ERROR: error in {}.".format(opt.config_file))
    exit(1)
# make routes.
app = web.Application(logger=logger)
app.router.add_route("GET", "/crest", provide_feeder_handler)
app.router.add_route("POST", "/beak", receive_feeder_handler)
app.router.add_route("GET", "/spawn", provide_json_handler)
app.router.add_route("GET", "/hatch", provide_rdf_handler)
app.router.add_route("GET", "/image/{name:.*\.png}", get_doc_handler)
app.router.add_route("GET", "/{name:.*\.(js|css|ico|map)}", get_doc_handler)
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
                                 ssl=config.get(CONF_SSL_CTX))
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
