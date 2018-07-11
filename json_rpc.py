#_*_ coding: utf-8 _*_

# 高速 list
from collections import deque
import logging
import logging.handlers
import time
import json
import websocket
import threading

class JsonRpc:
    def __init__(self):
        #config.jsonの読み込み
        f = open('config/config.json', 'r', encoding="utf-8")
        config = json.load(f)
        self._executions = deque(maxlen=300)
        self._spotExecutions = deque(maxlen=300)
        # self.key = config["key"]
        # self.secret = config["secret"]

    @property
    def executions(self):
        return self._executions
    @executions.setter
    def executions(self, val):
        self._executions = val

    def executionsWebsocket(self):
        """
        Websocketで価格を取得する場合の処理
        """
        executions = self.executions
        def on_message(ws, message):
            messages = json.loads(message)
            execution = messages["params"]["message"]
            for i in execution:
                executions.append(i)

        def on_error(ws, error):
            logging.error(error)

        def on_close(ws):
            while True:
                time.sleep(3)
                try:
                    ws = websocket.WebSocketApp("wss://ws.lightstream.bitflyer.com/json-rpc",
                                                on_message = on_message,
                                                on_error = on_error,
                                                on_close = on_close)
                    ws.on_open = on_open
                    ws.run_forever()
                except Exception as e:
                    logging.error(e)

        def on_open(ws):
            ws.send(json.dumps({"method": "subscribe", "params": {"channel": "lightning_executions_FX_BTC_JPY"}}))

        ws = websocket.WebSocketApp("wss://ws.lightstream.bitflyer.com/json-rpc",
                                    on_message = on_message,
                                    on_error = on_error,
                                    on_close = on_close)
        ws.on_open = on_open
        websocketThread = threading.Thread(target=ws.run_forever)
        websocketThread.start()

    def loop(self):
        self.executionsWebsocket()

        for i in range(10):
            if len(self.executions) == 0:
                logging.info("No Socket")
                time.sleep(1)
                continue
            
            logging.info("{} {}".format(i, len(self.executions)))
            logging.info("{} {}".format(i, self.executions[-1]))
            time.sleep(2)

        logging.info(self.executions)

if __name__ == '__main__':
    #logging設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    logfile=logging.handlers.TimedRotatingFileHandler(
        filename = 'log/json_rpc.log',
        when = 'midnight'
    )
    logfile.setLevel(logging.INFO)
    logfile.setFormatter(logging.Formatter(
        fmt='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'))
    logging.getLogger('').addHandler(logfile)
    logging.info('Wait...')

    jsocket = JsonRpc()
    jsocket.loop()