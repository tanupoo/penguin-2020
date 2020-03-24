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
CONF_OPT_DEBUG = "opt_debug"
CONF_TZ = "tz"
CONF_DEFAULT_SERVER_PORT = "65481"
CONF_SSL_CTX = "__ssl_ctx"
CONF_DB_CONN = "__db_conn"

LOG_FMT = "%(asctime)s.%(msecs)d %(lineno)d %(message)s"
LOG_DATE_FMT = "%Y-%m-%dT%H:%M:%S"

ws_map = {}

def common_access_log(request):
    logger.info("Access from {} {} {}".format(request.remote,
                                              request.message.method,
                                              request.message.url))

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
    """
    e.g.
        from db_connector_mongodb import db_connector

        p = handler(logger=self.logger, debug_level=self.debug_level,
                   db_connect="parameter_for_connect")
        p.submit(kv_data)

    e.g. of <parameter_for_connect>
        host=127.0.0.1 port=5432 dbname=postgres user=demo password=demo1
    """
    def __init__(self, **kwargs):
        """
        kwargs should contain: logger, debug_level
        """
        self.logger = kwargs.get("logger")
        self.debug_level = kwargs.get("debug_level", 0)
        self.tz = kwargs.get("tz", "GMT")
        self.db_init(**kwargs)

    def db_init(self, **kwargs):
        """
        db_name: default is "lorawan".
        db_collection: default is "sensors".
        db_addr: default is "localhost".
        db_port: default is 27017.
        db_timeout: default is 2000. (2 sec)
        """
        self.db_name = kwargs.setdefault("db_name", "plod")
        self.db_col_name = kwargs.setdefault("db_collection", "draft")
        self.db_addr = kwargs.setdefault("db_addr", "localhost")
        self.db_port = kwargs.setdefault("db_port", 27017)
        # XXX
        self.db_username = kwargs.setdefault("db_username", "root")
        self.db_password = kwargs.setdefault("db_upassword", "example")
        timeout = kwargs.setdefault("db_timeout", 2000)
        self.logger.info(f"""Connect MongoDB on {self.db_addr}:{self.db_port}
                         for {self.db_name}.{self.db_col_name}""")
        self.con = MongoClient(self.db_addr, self.db_port,
                               serverSelectionTimeoutMS=timeout,
                               username=self.db_username,
                               password=self.db_password)
        self.db = self.con[self.db_name]
        self.col = self.db[self.db_col_name]
        return True

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

async def feed_handler(request):
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
    print("kv_data", json.dumps(kv_data))

    # submit kv_data into database if needed.
    if config[CONF_DB_CONN]:
        logger.debug("db_submit() will be called.")
        if config[CONF_DB_CONN].db_submit(kv_data):
            logger.info(f"Submited kv_data for {event_id} successfully.")
        # even if error, proceed next anyway.
        # remove ObjectID("...") from kv_data as MongoDB adds "_id":ObjectID().
        if kv_data.get("_id"):
            kv_data.pop("_id")
    #
    return gen_http_response({"status":"success", "event_id":event_id})

async def hatch_handler(request):
    pass

async def spawn_handler(request):
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
    # make ssl context.
    logger.debug(f"cert specified: {config.get(CONF_SERVER_CERT)}")
    if config.get(CONF_SERVER_CERT):
        config[CONF_SSL_CTX] = ssl.create_default_context(
                ssl.Purpose.CLIENT_AUTH)
        config[CONF_SSL_CTX].load_cert_chain(config[CONF_SERVER_CERT])
    #
    config[CONF_DB_CONN] = db_connector(
            logger=logger,
            tz=config[CONF_TZ],
            debug_level=config[CONF_DEBUG_LEVEL])
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
app.router.add_route("POST", "/feed", feed_handler)
app.router.add_route("GET", "/spawn", spawn_handler)
app.router.add_route("GET", "/hatch", hatch_handler)
app.router.add_route("GET", "/{tail:.*}", get_doc_handler)
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
