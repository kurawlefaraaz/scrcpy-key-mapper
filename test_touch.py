import socket
import os
import struct
import json
from pynput import keyboard

class ScrcpyInfiniteMapper:
    def __init__(self, host='127.0.0.1', port=1234, sw=1920, sh=1080):
        self.host = host
        self.port = port
        self.sw = sw
        self.sh = sh
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.key_map = {}
        self.active_keys = {} 
        self.exit_key = 'esc'

    def connect(self):
        try:
            self.sock.connect((self.host, self.port))
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            print(f"[*] Connected! Multi-Touch Active. Press '{self.exit_key}' to quit.")
        except Exception as e:
            print(f"[!] Connection Error: {e}")
            exit(1)

    def load_json_map(self, json_data):
        data = json.loads(json_data)
        for index, node in enumerate(data['keyMapNodes']):
            name = node['key'].lower()
            self.key_map[name] = {
                "x": int(node['pos']['x']), 
                "y": int(node['pos']['y']), 
                "pid": index + 10 
            }
        print(f"[*] Loaded {len(self.key_map)} points.")

    def get_key_name(self, key):
        if hasattr(key, 'char') and key.char is not None:
            return key.char.lower()
        name = getattr(key, 'name', str(key)).lower()
        if 'ctrl' in name: return 'ctrl'
        if 'alt' in name: return 'alt'
        if 'shift' in name: return 'shift'
        if 'space' in name: return 'space'
        return name

    def send_touch(self, x, y, action, pointer_id):
        msg_type = 2
        
        # DOWN (0) or MOVE (2)
        if action in (0, 2):
            pressure = 65535
            buttons = 1  # Primary button
        # UP (1)
        else:
            pressure = 0
            buttons = 0  # CRITICAL: No buttons/pressure on release

        # scrcpy expects: Type, Action, PID, X, Y, W, H, Pressure, ActionButtons, Buttons
        msg = struct.pack('>BBQIIHHHII',
                          msg_type, action, pointer_id,
                          x, y, self.sw, self.sh,
                          pressure, 1 if action == 0 else 0, buttons)
        self.sock.sendall(msg)

    def on_press(self, key):
        k = self.get_key_name(key)
        if k == self.exit_key:
            self.release_all()
            os._exit(0)

        if k in self.key_map and k not in self.active_keys:
            data = self.key_map[k]
            self.active_keys[k] = data['pid']
            self.send_touch(data['x'], data['y'], 0, data['pid']) # Action 0: DOWN

    def on_release(self, key):
        k = self.get_key_name(key)
        
        if k in self.active_keys:
            # 1. Grab the pointer ID we assigned when it was pressed
            pid = self.active_keys[k]
            data = self.key_map[k]
            
            # 2. Send the UP event at the same location with 0 pressure
            # We use the PID stored in active_keys to ensure consistency
            self.send_touch(data['x'], data['y'], 1, pid) 
            
            # 3. NOW remove it from the tracker
            # This prevents the 'repeat' logic from getting confused
            del self.active_keys[k]
            print(f"[-] Released {k} (PID: {pid})")

    def release_all(self):
        for k, pid in list(self.active_keys.items()):
            data = self.key_map[k]
            self.send_touch(data['x'], data['y'], 1, pid)
        self.active_keys.clear()

# --- Mappings ---
JSON_MAP = """
{
  "keyMapNodes": [
    {"key": "w", "pos": {"x": 1807, "y": 902}},
    {"key": "s", "pos": {"x": 1643, "y": 902}},
    {"key": "a", "pos": {"x": 120, "y": 902}},
    {"key": "d", "pos": {"x": 328, "y": 902}},
    {"key": "space", "pos": {"x": 903, "y": 1052}},
    {"key": "shift", "pos": {"x": 1848, "y": 501}},
    {"key": "ctrl", "pos": {"x": 1848, "y": 601}}
  ]
}
"""

if __name__ == "__main__":
    mapper = ScrcpyInfiniteMapper(sw=1920, sh=1080)
    mapper.load_json_map(JSON_MAP)
    mapper.connect()
    
    with keyboard.Listener(on_press=mapper.on_press, on_release=mapper.on_release) as listener:
        listener.join()
