import os
from .base import *
# you need to set "myproject = 'prod'" as an environment variable
# in your OS (on which your website is hosted)

os.environ["PLATFORM"] = "dev"

if os.environ.get("PLATFORM") == 'prod':
   from .prod import *
elif os.environ.get("PLATFORM") == "stage":
   from .stage import *
else:
   from .dev import *
