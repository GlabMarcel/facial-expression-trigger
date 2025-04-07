import json
import os

class ConfigManager:
    DEFAULT_CONFIG = {
        "settings": {
            "hold_frames": 5
        },
        "thresholds": {
            "mouth_open": 0.35,
            "eyebrows_raised": 0.28,
            "smile": 0.35,
            "left_wink": 0.20,
            "right_wink": 0.20
        },
        "actions": {
            "mouth_open": {"type": "press", "value": "a"},
            "eyebrows_raised": {"type": "press", "value": "enter"},
            "smile": {"type": "write", "value": ":)"},
            "left_wink": None,
            "right_wink": None
        },
        "enabled_gestures": {
            "mouth_open": True,
            "eyebrows_raised": True,
            "smile": True,
            "left_wink": True,
            "right_wink": True
        }
    }

    def __init__(self, config_filename="config.json"):
        script_dir = os.path.dirname(os.path.realpath(__file__))
        self.config_path = os.path.join(script_dir, "..", config_filename)
        self.config_data = self._load()
        print(f"ConfigManager initialized. Config path: {self.config_path}")
        self._sync_monitored_expressions()

    def _sync_monitored_expressions(self):
        threshold_keys = set(self.config_data.get("thresholds", {}).keys())
        actions = self.config_data.setdefault("actions", {})
        enabled = self.config_data.setdefault("enabled_gestures", {})
        default_actions = self.DEFAULT_CONFIG.get("actions", {})
        default_enabled = self.DEFAULT_CONFIG.get("enabled_gestures", {})

        for key in threshold_keys:
            actions.setdefault(key, default_actions.get(key, None))
            enabled.setdefault(key, default_enabled.get(key, True))

        action_keys_to_remove = [k for k in actions if k not in threshold_keys]
        for k in action_keys_to_remove: del actions[k]
        enabled_keys_to_remove = [k for k in enabled if k not in threshold_keys]
        for k in enabled_keys_to_remove: del enabled[k]

    def _load(self):
        print(f"Attempting to load configuration from: {self.config_path}")
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            config_data = json.loads(json.dumps(self.DEFAULT_CONFIG))
            for section, defaults in self.DEFAULT_CONFIG.items():
                loaded_section_data = loaded_data.get(section, {})
                config_section = config_data.setdefault(section, {})
                if isinstance(loaded_section_data, dict):
                    for key, value in defaults.items():
                        loaded_section_data.setdefault(key, value)
                    config_section.update(loaded_section_data)

            print("Configuration loaded and merged with defaults.")
            return config_data
        except FileNotFoundError:
            print(f"Warning: Config file '{os.path.basename(self.config_path)}' not found. Creating with default values.")
            default_data = self.DEFAULT_CONFIG.copy()
            if self._save_internal(default_data):
                print("Default configuration file created.")
                return default_data
            else:
                print("Error: Could not create default config file. Using in-memory defaults.")
                return self.DEFAULT_CONFIG.copy()
        except (json.JSONDecodeError, Exception) as e:
            print(f"Warning/Error loading config file: {e}. Using default values.")
            return self.DEFAULT_CONFIG.copy()

    def _save_internal(self, data_to_save):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving configuration internally: {e}")
            return False

    def save(self):
        self._sync_monitored_expressions()
        if self._save_internal(self.config_data):
            print(f"Configuration successfully saved to {self.config_path}")
            return True
        else:
            print(f"Error saving configuration to {self.config_path}")
            return False

    def get_config(self): return self.config_data
    def get_thresholds(self): return self.config_data.get("thresholds", {})
    def get_actions(self): return self.config_data.get("actions", {})
    def get_enabled_gestures(self):
        return self.config_data.get("enabled_gestures", {})
    def get_setting(self, key, default=None):
        default_value = self.DEFAULT_CONFIG.get("settings", {}).get(key, default)
        return self.config_data.get("settings", {}).get(key, default_value)

    def get_threshold(self, key, default=None):
        default_value = self.DEFAULT_CONFIG.get("thresholds", {}).get(key, default)
        return self.get_thresholds().get(key, default_value)

    def get_action(self, key):
        default_value = self.DEFAULT_CONFIG.get("actions", {}).get(key, None)
        return self.get_actions().get(key, default_value)

    def update_thresholds(self, new_thresholds_dict):
        self.config_data.setdefault("thresholds", {}).update(new_thresholds_dict)
        print(f"Updating thresholds in config: {new_thresholds_dict}")
        return self.save()

    def update_actions(self, new_actions_dict):
        self.config_data["actions"] = new_actions_dict
        print(f"Updating actions in config: {new_actions_dict}")
        return self.save()

    def update_action(self, key, action_config):
        self.config_data.setdefault("actions", {})[key] = action_config
        print(f"Updating action '{key}' in config: {action_config}")
        return self.save()

    def update_gesture_enabled(self, key, is_enabled):
        self.config_data.setdefault("enabled_gestures", {})[key] = bool(is_enabled)
        print(f"Updating enabled status for '{key}' to {is_enabled}")
        return self.save()

    def update_setting(self, key, value):
        self.config_data.setdefault("settings", {})[key] = value
        print(f"Updating setting '{key}' in config to {value}")
        return self.save()