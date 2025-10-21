from langchain_openai import ChatOpenAI
import time, os
from datetime import datetime
import math

class ThrottledChatOpenAI(ChatOpenAI):
    _tpm = None                 # 默认 TPM，可在构造函数里覆盖
    _prev_time = None
    _prev_token_count = None
    # for siliconflow, the rule is after my input(which could have more token then TPM at first)
    # must have enough cool down time to ensure before next input the time * tpm 
    # is enough to cover the first input&output token count
    def __init__(self, *, tpm: str="1000000", **kw):
        # super init first to ensure all attributes are set
        super().__init__(**kw)
        self._tpm = int(tpm)
        print(f"[TPM throttle {datetime.now()}] tpm: {self._tpm}")
    def invoke(self, messages, config=None, **kw):
        if self._prev_time is None and self._prev_token_count is None:
            self._prev_time = datetime.now()
            print(f"[TPM throttle {self._prev_time}] invoking llm")
            response = super().invoke(messages, config=config, **kw)
            self._prev_token_count = response.usage_metadata["total_tokens"]
            print(f"[TPM throttle {datetime.now()}] input+output {self._prev_token_count} tokens used")
            return response
        else:
            print(f"[TPM throttle {datetime.now()}] invoking llm")
            now = datetime.now()
            # calculate time from previous output
            time_diff = (now - self._prev_time).total_seconds()/60
            # Want to ensure give previous output enough cool down time
            token_buffer = self._tpm * time_diff
            if self._prev_token_count > token_buffer:
                pause_time = math.ceil((self._prev_token_count - token_buffer)/self._tpm)
                print(f"[TPM throttle {now}] prev time {self._prev_time}, prev token {self._prev_token_count},")
                print(f"[TPM throttle {now}] time_diff {time_diff}, token_buffer {token_buffer},")
                print(f"[TPM throttle {now}] need to sleep {pause_time} minutes to cover prev_token_count - token_buffer: {self._prev_token_count - token_buffer}")
                time.sleep(pause_time * 60)
            self._prev_time = datetime.now()
            response = super().invoke(messages, config=config, **kw)
            self._prev_token_count = response.usage_metadata["total_tokens"]
            return response
            


