# import os
# import logging
# from pathlib import Path
#
# # specify the default value and an environment variable which would be
# # overwriting
# LOGFORMAT = '%(asctime)s|%(name)s|%(levelname)s|%(message)s'
#
#
# def set_log_file(logger: logging.Logger, fpath: Path):
#     """ Overwrite the file handler in the logger """
#     for hdl in logger.handlers:
#         if isinstance(hdl, logging.FileHandler):
#             logger.removeHandler(hdl)
#             logger.root.removeHandler(hdl)
#
#     new_fh = logging.FileHandler(fpath)
#     formatter = logging.Formatter(LOGFORMAT)
#     new_fh.setFormatter(formatter)
#
#     logger.addHandler(new_fh)
#
#
# logcfg = dict(
#     level=logging.WARNING,
#     format=LOGFORMAT,
# )
#
# # if evironment variables are defined use them and overwrite default
# os_envs = dict(
#     filename='PYTHON_LOGGING_DIR',
#     level='PYTHON_LOGGING_LEVEL'
# )
#
# for k, v in os_envs.items():
#     try:
#         logcfg[k] = os.environ[v]
#     except KeyError:
#         pass
#
# logging.basicConfig(**logcfg)
#
# logger = logging.getLogger("control_room")
#
#
# # --> No streamhandler needed as root logger already has one
# # # For now always add a stream handler
# # streamhandler = logging.StreamHandler()
# # streamhandler.setFormatter(
# #     logging.Formatter(logcfg['format'])
# # )
# # logger.addHandler(streamhandler)
#
#
# # File handler - assume there will always be only one log file!
# filename = Path('./dareplane.log').resolve()
# set_log_file(logger, filename)
#
#
# if __name__ == '__main__':
#     logger.debug("Debugging message")
#     logger.info("Info message")
#     logger.warning("warning message")
#     logger.error("error message")
#     logger.critical("critical message")

import yaml
import logging
import logging.config

logging.config.dictConfig(
    yaml.load(open("./configs/logger_config.yaml", "r"), Loader=yaml.FullLoader)
)
logger = logging.getLogger("control_room")
