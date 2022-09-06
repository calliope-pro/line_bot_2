from linebot import __version__ as linebot_version
from .http_client import AioHttpResponse, AioHttpClient
from .builder import AioLineBotApiBuilder

# provide alternative attribute of linebot.__version__
__version__ = "0.4.1"

try:
    from .api import AioLineBotApi
    if AioLineBotApi.LINE_BOT_API_VERSION != linebot_version:
        print("Updating AioLineBotApi from LineBotApi version " + linebot_version)
        AioLineBotApiBuilder.build_class("/tmp/api.py", linebot_version)
        from .api import AioLineBotApi
        print("Done!")

except Exception:
    print("Creating AioLineBotApi from LineBotApi version " + linebot_version)
    AioLineBotApiBuilder.build_class("/tmp/api.py", linebot_version)
    from .api import AioLineBotApi
    print("Done!")
