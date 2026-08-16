import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_tmp = tempfile.mkdtemp(prefix="helper_recall_test_")
os.chdir(_tmp)
os.environ["DRIVER"] = "~none"

import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OnebotV11Adapter

nonebot.init()
driver = nonebot.get_driver()
driver.register_adapter(OnebotV11Adapter)
nonebot.load_plugin("nonebot_plugin_helper_recall")
