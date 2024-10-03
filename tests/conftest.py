import pytest
import shutil
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    config.option.tbstyle = 'short'
    # logger.info("Starting test session")

@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    # logger.info("Test session finished")

    # Remove the __pycache__ directory
    shutil.rmtree('__pycache__', ignore_errors=True)
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                shutil.rmtree(os.path.join(root, dir_name), ignore_errors=True)
                logger.info(f"Removed __pycache__ directory: {os.path.join(root, dir_name)}")
