import os
import logging
import timber

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.addHandler(logging.StreamHandler())

timber_handler = timber.TimberHandler(source_id=os.environ['TIMBER_SOURCE_ID'], api_key=os.environ['TIMBER_API_KEY'])
logger.addHandler(timber_handler)


