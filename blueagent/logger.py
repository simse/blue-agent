import os
import logging
import timber

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.addHandler(logging.StreamHandler())

timber_handler = timber.TimberHandler(api_key=os.environ['TIMBER_API_KEY'])
logger.addHandler(timber_handler)


