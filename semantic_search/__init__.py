import logging

# Configure logging similar to other modules in this repository.  This ensures
# that when the package is imported directly, users see helpful information
# about what the code is doing.
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
