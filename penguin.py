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
from pymongo import ReturnDocument
import uuid
from json2turtle import plod_json2turtle
from bson.objectid import ObjectId
import re

__CONF_SSL_CTX = "__ssl_ctx"
__CONF_DB_CONN = "__db_conn"

re_db_reportid = re.compile("^[\-a-f0-9]+$")

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
def dumps_utf8(data):
    return json.dumps(data, ensure_ascii=False)

def http_response_turtle(msg, filename=None):
    http_response_logging(msg)
    # XXX shout put Content-Disposition: attachment; filename=filename
    return web.Response(body=msg, content_type="text/turtle; charset=utf-8")

def http_response_json(msg, filename=None):
    http_response_logging(msg)
    # XXX shout put Content-Disposition: attachment; filename=filename
    return web.json_response(msg, dumps=dumps_utf8)

def http_response(msg, status=200, log_text=None):
    http_response_logging(msg, status=status, log_text=log_text)
    return web.json_response({"result":msg}, status=status, dumps=dumps_utf8)

def http_response_logging(msg, status=200, log_text=None):
    if status != 200:
        logger.error("{} status={} error={}".format(msg, status, log_text))
    else:
        if config[CONF_DEBUG_LEVEL] > 1:
            logger.debug("result {} status={}".format(msg, status))
        else:
            logger.debug("result {} bytes status={}".format(len(msg), status))

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
        self.logger.info("Connected to MongoDB {}.{} on {}:{}".
                         format(self.config[CONF_DB_NAME],
                                self.config[CONF_DB_COLLECTION],
                                self.config[CONF_DB_ADDR],
                                self.config[CONF_DB_PORT]))

    def submit(self, kv_data, **kwargs):
        try:
            # report_id (UUID4) is the unique key.
            #ret = self.col.update_one({"_id":kv_data["_id"]}, kv_data,
            #                          upsert=True)
            report_id = kv_data["reportId"]
            ret = self.col.find_one_and_replace({"reportId":report_id},
                                                kv_data, upsert=True,
                                        return_document=ReturnDocument.AFTER)
            print("xxx", ret)
            self.logger.debug("DB: Inserted: reportId={} _id={}"
                              .format(ret["reportId"], ret["_id"]))
            return True
        except pymongo.errors.ServerSelectionTimeoutError as e:
            self.logger.error("DB: timeout, DB looks not ready yet.")
            return False

    def delete(self, report_id, **kwargs):
        try:
            ret = self.col.delete_one({"reportId":report_id})
            if ret.deleted_count == 0:
                self.logger.debug(f"DB: no such a report {report_id}.")
                return False
            else:
                self.logger.debug(f"DB: Deleted: {report_id}")
                return True
        except pymongo.errors.ServerSelectionTimeoutError as e:
            self.logger.error("DB: timeout, DB looks not ready yet.")
            return False

    def find(self, selector):
        """
        selector: dict
           replace ObjectID(_id) into _id.
        """
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
def common_access_log(request):
    """
    logger.info("Access from {} {} {}".format(request.remote,
                                              request.method,
                                              request.url))
    """
    pass

def debug_http_message(headers, content):
    if config[CONF_DEBUG_LEVEL] > 1:
        logger.debug("---BEGIN OF REQUESTED HEADER---")
        for k,v in headers.items():
            logger.debug("{}: {}".format(k,v))
        logger.debug("---END OF REQUESTED HEADER---")
    if config[CONF_DEBUG_LEVEL] > 1:
        logger.debug("---BEGIN OF REQUESTED DATA---")
        logger.debug(content)
        logger.debug("---END OF REQUESTED DATA---")

async def provide_listview_handler(request):
    """
    all document must be placed under the ui directory.
    """
    common_access_log(request)
    path = "./ui/listview.html"
    logger.debug("DEBUG: serving {}".format(path))
    if os.path.exists(path):
        return web.FileResponse(path)
    else:
        raise web.HTTPNotFound()

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

async def receive_plod_bulk_handler(request):
    """
    Note that it doesn't assign reportId.
    """
    common_access_log(request)
    try:
        if not request.can_read_body:
            return http_response("the body can not be read.", status=400)
        content = await request.json()
    except json.decoder.JSONDecodeError as e:
        return http_response("The payload format was not likely JSON.",
                status=502, log_text=str(e))
    debug_http_message(request.headers, content)
    #
    if not config[__CONF_DB_CONN]:
        return http_response("DB hasn't been ready.", status=503)
    # need more sanity check
    for plod in content:
        report_id = plod.get("reportId")
        if report_id is None:
            return http_response("invalid data.", status=400)
        # removing _id if exists for sure.
        if plod.get("_id"):
            plod.pop("_id")
    for plod in content:
        report_id = plod.get("reportId")
        logger.debug("submit data: {}".format(json.dumps(plod)))
        if not config[__CONF_DB_CONN].submit(plod):
            return http_response("Registration failed.", status=503)
        #
        logger.info(f"Submited data: {report_id}")
    return http_response("success")

async def receive_plod_handler(request):
    common_access_log(request)
    try:
        if not request.can_read_body:
            return http_response("the body can not be read.", status=400)
        content = await request.json()
    except json.decoder.JSONDecodeError as e:
        return http_response("The payload format was not likely JSON.",
                status=502, log_text=str(e))
    debug_http_message(request.headers, content)
    #
    if not config[__CONF_DB_CONN]:
        return http_response("DB hasn't been ready.", status=503)
    ## sanity check.
    #if check_valid_data(content) is False:
    #    return http_response("The content was not likely PLOD.", status=502)
    # assign new reportId.
    report_id = content.setdefault("reportId", str(uuid.uuid4()))
    logger.debug("submit data: {}".format(json.dumps(content)))
    if not config[__CONF_DB_CONN].submit(content):
        return http_response("Registration failed.", status=503)
    #
    logger.info(f"Submited data: {report_id}")
    ## if you use content, you need to care aboout "_id":ObjectID().
    if content.get("_id"):
        _id = str(content.pop("_id"))
        content.update({"_id": f"{_id}"})
    return http_response({"data":content})

async def delete_plod_handler(request):
    common_access_log(request)
    #
    condition = request.match_info["cond"]
    if re_db_reportid.match(condition):
        logger.debug("delete data reportId: {condition}")
        report_id = condition
    else:
        return http_response(f"invalid request", status=400)
    #
    if not config[__CONF_DB_CONN]:
        return http_response("DB hasn't been ready.", status=503)
    if not config[__CONF_DB_CONN].delete(report_id):
        return http_response("Delete failed.", status=503)
    logger.info(f"Delete successfully {report_id}.")
    return http_response("success")

async def provide_plod_handler(request):
    common_access_log(request)
    #
    output_format = request.match_info["fmt"]
    if output_format not in ["json", "turtle"]:
        return http_response(f"{output_format} is not supported.", status=415)
    if request.method == "POST":
        if not request.can_read_body:
            return http_response("the body can not be read.", status=400)
        try:
            content = await request.json()
        except json.decoder.JSONDecodeError as e:
            return http_response("The payload format was not likely JSON.",
                    status=502, log_text=str(e))
        debug_http_message(request.headers, content)
        db_filter = await request.json()
    elif request.method == "GET":
        condition = request.match_info["cond"]
        """
        condition: string like
            "5e7d9ace0810c91d43c60130" => { "_id": ObjectID("...") }
            "1ef3c491-a892-4410-b4db-dc755c656cd1" => { "reportId": "..." }
            '{ "any_key": "any_value" }' => { "any_key": "any_value" }
            "all" => {}
            # not used: "{}" => {}
            # not used:  None => {}
        """
        if condition == "all":
            db_filter = {}
        elif re_db_reportid.match(condition):
            db_filter = { "reportId": condition }
        else:
            return http_response(f"invalid request", status=400)
    else:
        return http_response(f"{request.method} is not supported.", status=405)
    #
    if not config[__CONF_DB_CONN]:
        return http_response("DB hasn't been ready.", status=503)
    # XXX should check the condition here ?
    logger.debug(f"Try seraching db by [{db_filter}]")
    # XXX should be await, but how ?
    result = config[__CONF_DB_CONN].find(db_filter)
    if result[0] == False:
        return http_response("{}.".format(result[1]), status=503)
    if output_format == "json":
        return http_response_json(result[1])
    elif output_format == "turtle":
        return http_response_turtle(plod_json2turtle(result[1]))

#
# logging
#
def set_logger(log_file=None, logging_stdout=False, debug_mode=False):
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
app.router.add_route("POST", "/beak/bulk", receive_plod_bulk_handler)
app.router.add_route("POST", "/beak", receive_plod_handler)
app.router.add_route("DELETE", "/tail/{cond:.+}", delete_plod_handler)
app.router.add_route("GET", "/tummy/{fmt:(json|turtle)}/{cond:.+}", provide_plod_handler)
app.router.add_route("POST", "/tummy/{fmt:(json|turtle)}", provide_plod_handler)
app.router.add_route("GET", "/tummy", provide_listview_handler)
app.router.add_route("GET", "/images/{name:.+\.(png)}", get_doc_handler)
app.router.add_route("GET", "/js/{name:.+\.(js|css|map)}", get_doc_handler)
app.router.add_route("GET", "/favicon.ico", get_doc_handler)
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
