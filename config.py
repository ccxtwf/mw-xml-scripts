import logging

"""
Logging Utils
"""
logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


"""
The maximum number of <page> node elements to unpack from the XML dump at a time.
Adjust based on the average size of your pages on your wiki and based on your RAM.
"""
MAX_PAGE_NODES_TO_UNPACK=100