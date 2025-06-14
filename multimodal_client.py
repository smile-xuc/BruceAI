import base64
import json
from dataclasses import dataclass, field
from typing import Optional, List

import websocket

# Data classes based on documentation
@dataclass
class Upstream:
    type: str
    mode: str = "push2talk"
    audio_format: str = "pcm"

@dataclass
class Downstream:
    voice: Optional[str] = None
    sample_rate: Optional[int] = None

@dataclass
class Device:
    uuid: str

@dataclass
class ClientInfo:
    user_id: str
    device: Device

@dataclass
class RequestParameters:
    upstream: Upstream
    downstream: Downstream
    client_info: ClientInfo
    sandbox: bool = False
    directive: str = "Start"
    dialog_id: Optional[str] = None

@dataclass
class RequestToRespondParameters:
    images: Optional[List[dict]] = field(default_factory=list)

class MultiModalCallback:
    """Callbacks for multimodal interaction."""

    def on_started(self, dialog_id: str) -> None:
        print("Dialog started", dialog_id)

    def on_stopped(self) -> None:
        print("Dialog stopped")

    def on_state_changed(self, state: str) -> None:
        print("State changed", state)

    def on_speech_audio_data(self, data: bytes) -> None:
        print(f"Received {len(data)} bytes of audio")

    def on_error(self, error) -> None:
        print("Error", error)

    def on_connected(self) -> None:
        print("Connected to server")

    def on_responding_started(self):
        print("Responding started")

    def on_responding_ended(self):
        print("Responding ended")

    def on_speech_content(self, payload):
        print("Speech text", payload)

    def on_responding_content(self, payload):
        print("Model reply", payload)

    def on_request_accepted(self):
        print("Interrupt accepted")

    def on_close(self, code, msg):
        print("Connection closed", code, msg)

class MultiModalDialog:
    """Simple websocket client following documentation."""

    def __init__(self, *, workspace_id: str, app_id: str, request_params: RequestParameters,
                 multimodal_callback: MultiModalCallback, url: str, api_key: str,
                 dialog_id: Optional[str] = None, model: Optional[str] = None):
        self.workspace_id = workspace_id
        self.app_id = app_id
        self.request_params = request_params
        self.callback = multimodal_callback
        self.url = url
        self.api_key = api_key
        self.dialog_id = dialog_id
        self.model = model
        self.ws: Optional[websocket.WebSocketApp] = None

    def start(self, dialog_id: Optional[str] = None):
        self.dialog_id = dialog_id or self.dialog_id
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-DashScope-Workspace": self.workspace_id,
            "X-DashScope-AppId": self.app_id,
        }
        self.ws = websocket.WebSocketApp(
            self.url,
            header=[f"{k}: {v}" for k, v in headers.items()],
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        self.ws.run_forever()

    def _on_open(self, ws):
        self.callback.on_connected()
        start_payload = {
            "action": "start",
            "params": json.dumps(self.request_params, default=lambda o: o.__dict__),
        }
        ws.send(json.dumps(start_payload))
        self.callback.on_started(self.dialog_id or "")

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            data = {}
        action = data.get("action")
        if action == "speech_audio":
            audio_data = base64.b64decode(data.get("data", ""))
            self.callback.on_speech_audio_data(audio_data)
        elif action == "speech_text":
            self.callback.on_speech_content(data.get("text"))
        elif action == "reply_text":
            self.callback.on_responding_content(data.get("text"))
        elif action == "state":
            self.callback.on_state_changed(data.get("state"))
        elif action == "close":
            ws.close()

    def _on_error(self, ws, error):
        self.callback.on_error(error)

    def _on_close(self, ws, code, msg):
        self.callback.on_close(code, msg)

    def start_speech(self):
        if self.ws:
            self.ws.send(json.dumps({"action": "start_speech"}))

    def send_audio_data(self, speech_data: bytes):
        if self.ws:
            encoded = base64.b64encode(speech_data).decode()
            self.ws.send(json.dumps({"action": "audio", "data": encoded}))

    def stop_speech(self):
        if self.ws:
            self.ws.send(json.dumps({"action": "stop_speech"}))

    def interrupt(self):
        if self.ws:
            self.ws.send(json.dumps({"action": "interrupt"}))

    def local_responding_started(self):
        if self.ws:
            self.ws.send(json.dumps({"action": "local_responding_started"}))

    def local_responding_ended(self):
        if self.ws:
            self.ws.send(json.dumps({"action": "local_responding_ended"}))

    def stop(self):
        if self.ws:
            self.ws.send(json.dumps({"action": "stop"}))

    def get_dialog_state(self):
        if self.ws:
            self.ws.send(json.dumps({"action": "get_state"}))

    def request_to_respond(self, request_type: str, text: str,
                            parameters: Optional[RequestToRespondParameters] = None):
        if self.ws:
            payload = {
                "action": "request_to_respond",
                "type": request_type,
                "text": text,
                "params": parameters.__dict__ if parameters else {},
            }
            self.ws.send(json.dumps(payload))

if __name__ == "__main__":
    # Example usage. Replace placeholders with real credentials.
    up_stream = Upstream(type="AudioOnly", mode="push2talk", audio_format="pcm")
    down_stream = Downstream(sample_rate=48000)
    device = Device(uuid="1234567890")
    client_info = ClientInfo(user_id="aabb", device=device)
    request_params = RequestParameters(upstream=up_stream,
                                       downstream=down_stream,
                                       client_info=client_info)

    callback = MultiModalCallback()
    dialog = MultiModalDialog(
        workspace_id="YOUR_WORKSPACE_ID",
        app_id="YOUR_APP_ID",
        request_params=request_params,
        multimodal_callback=callback,
        url="wss://dashscope.aliyuncs.com/api/v1/multimodal/dialog",
        api_key="YOUR_API_KEY",
    )
    dialog.start()
