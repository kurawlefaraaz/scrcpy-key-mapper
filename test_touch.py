import socket
import struct
import json
from pynput import keyboard

class ScrcpyInfiniteMapper:
    def __init__(self, host='127.0.0.1', port=1234, sw=2400, sh=1080):
        self.host = host
        self.port = port
        self.sw = sw
        self.sh = sh
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.key_map = {}
        self.active_keys = {} # Store key: pointer_id mapping
        self.enabled = True
        self.switch_key = 'backtick' 

    def connect(self):
        try:
            self.sock.connect((self.host, self.port))
            print(f"[*] Connected! Multi-Touch Active. Hold keys to keep buttons pressed.")
        except Exception as e:
            print(f"[!] Connection Error: {e}")
            exit(1)

    def load_json_map(self, json_data):
        data = json.loads(json_data)
        # Assign unique pointer IDs starting from 0 to each mapped key
        for index, node in enumerate(data['keyMapNodes']):
            raw_key = node['key'].replace("Key_", "").lower()
            px = int(node['pos']['x'] * self.sw)
            py = int(node['pos']['y'] * self.sh)
            
            self.key_map[raw_key] = {
                "x": px, 
                "y": py, 
                "comment": node['comment'], 
                "pid": index  # Unique 'finger' index
            }
        print(f"[*] Loaded {len(self.key_map)} unique touch points.")

    def send_touch(self, x, y, action, pointer_id):
        """v3.3.4 - 32-byte Control Message"""
        msg_type = 2
        pressure = 65535 if action in [0, 2] else 0
        btn = 1 if action in [0, 2] else 0
        
        # Structure: Type(1), Action(1), PID(8), X(4), Y(4), W(2), H(2), Pres(2), ActBtn(4), Btns(4)
        msg = struct.pack('>BBQIIHHHII', 
                          msg_type, action, pointer_id, 
                          x, y, self.sw, self.sh, 
                          pressure, btn, btn)
        self.sock.sendall(msg)

    def on_press(self, key):
        try:
            k = key.char.lower() if hasattr(key, 'char') else key.name.lower()
            
            if k == self.switch_key:
                self.enabled = not self.enabled
                print(f"\n[ SYSTEM ] Keymapper {'ENABLED' if self.enabled else 'DISABLED'}")
                if not self.enabled: self.release_all()
                return

            if self.enabled and k in self.key_map:
                if k not in self.active_keys:
                    # Key is pressed down for the first time
                    data = self.key_map[k]
                    self.active_keys[k] = data['pid']
                    print(f"[ HOLDING ] {data['comment']} (Finger {data['pid']})")
                    self.send_touch(data['x'], data['y'], 0, data['pid'])
                # If key is already in active_keys, pynput is just repeating the OS 'held' signal. 
                # We ignore it so we don't spam the server.
        except Exception: pass

    def on_release(self, key):
        try:
            k = key.char.lower() if hasattr(key, 'char') else key.name.lower()
            if k in self.active_keys:
                data = self.key_map[k]
                print(f"[ RELEASE ] {data['comment']} (Finger {data['pid']})")
                self.send_touch(data['x'], data['y'], 1, data['pid'])
                del self.active_keys[k]
        except Exception: pass

    def release_all(self):
        """Emergency release for all active touch points"""
        for k, pid in list(self.active_keys.items()):
            data = self.key_map[k]
            self.send_touch(data['x'], data['y'], 1, pid)
        self.active_keys.clear()
        print("[*] All touch points lifted.")

# --- Mappings ---
JSON_MAP = """
{
  "keyMapNodes": [
    {"comment": "W", "key": "Key_W", "pos": {"x": 0.9414, "y": 0.8357}},
    {"comment": "S", "key": "Key_S", "pos": {"x": 0.8558, "y": 0.8357}},
    {"comment": "Space", "key": "Key_Space", "pos": {"x": 0.4707, "y": 0.9749}},
    {"comment": "D", "key": "Key_D", "pos": {"x": 0.1712, "y": 0.8357}},
    {"comment": "A", "key": "Key_A", "pos": {"x": 0.1284, "y": 0.8357}},
    {"comment": "H", "key": "Key_H", "pos": {"x": 0.1498, "y": 0.7428}},
    {"comment": "E", "key": "Key_E", "pos": {"x": 0.2353, "y": 0.7428}},
    {"comment": "Q", "key": "Key_Q", "pos": {"x": 0.0642, "y": 0.7428}},
    {"comment": "Shift", "key": "Key_Shift", "pos": {"x": 0.9628, "y": 0.4643}},
    {"comment": "Alt", "key": "Key_Alt", "pos": {"x": 0.9628, "y": 0.5107}},
    {"comment": "Control", "key": "Key_Control", "pos": {"x": 0.9628, "y": 0.5571}}
  ]
}
"""

if __name__ == "__main__":
    # Ensure sw/sh match your device's orientation (Landscape usually means sw > sh)
    mapper = ScrcpyInfiniteMapper(sw=2400, sh=1080)
    mapper.load_json_map(JSON_MAP)
    mapper.connect()
    
    with keyboard.Listener(on_press=mapper.on_press, on_release=mapper.on_release) as listener:
        listener.join()