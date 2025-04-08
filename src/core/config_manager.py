# src/core/config_manager.py
import json
import os

class ConfigManager:
    DEFAULT_CONFIG = {
        "settings": {
            "hold_frames": 5
            # wink_hold_frames removed
        },
        "thresholds": {
            "mouth_open": 0.35,
            "eyebrows_raised": 0.28,
            "smile": 0.35
            # left_wink, right_wink removed
        },
        "actions": {
            "mouth_open": {"type": "press", "value": "a"},
            "eyebrows_raised": {"type": "press", "value": "enter"},
            "smile": {"type": "write", "value": ":)"}
            # left_wink, right_wink removed
        },
        "enabled_gestures": {
            "mouth_open": True,
            "eyebrows_raised": True,
            "smile": True
            # left_wink, right_wink removed
        }
    }

    def __init__(self, config_file_path="config.json"):
        if not os.path.dirname(config_file_path):
             script_dir = os.path.dirname(os.path.realpath(__file__))
             self.config_path = os.path.abspath(os.path.join(script_dir, "..", "..", config_file_path))
        else:
             self.config_path = os.path.abspath(config_file_path)
        self.config_data = self._load()
        print(f"ConfigManager initialized. Config path: {self.config_path}")
        self._sync_sections()

    def _sync_sections(self):
        needs_save = False
        threshold_keys = set(self.config_data.get("thresholds", {}).keys())
        default_threshold_keys = set(self.DEFAULT_CONFIG.get("thresholds", {}).keys())
        master_keys = threshold_keys.union(default_threshold_keys) # Use keys from both loaded and default

        for section, defaults in self.DEFAULT_CONFIG.items():
             if section != "thresholds": # Sync actions and enabled based on threshold keys
                 config_section = self.config_data.setdefault(section, {})
                 # Add missing default keys
                 for key in master_keys:
                      if key in defaults: # Check if default exists for this key
                          if key not in config_section:
                              config_section[key] = defaults[key]
                              needs_save = True
                 # Remove orphaned keys
                 keys_to_remove = [k for k in config_section if k not in master_keys and k in defaults]
                 for k in keys_to_remove:
                      del config_section[k]
                      needs_save = True
             elif section == "settings": # Ensure settings section has defaults
                  config_section = self.config_data.setdefault(section, {})
                  for key, value in defaults.items():
                       if key not in config_section:
                            config_section[key] = value
                            needs_save = True

    def _load(self):
        print(f"Attempting to load configuration from: {self.config_path}")
        loaded_data = {}
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            print("Configuration file found and loaded.")
        except FileNotFoundError:
            print(f"Warning: Config file '{os.path.basename(self.config_path)}' not found. Using defaults.")
            return json.loads(json.dumps(self.DEFAULT_CONFIG))
        except json.JSONDecodeError as e:
            print(f"Warning/Error loading config file: Invalid JSON - {e}. Using default values.")
            return json.loads(json.dumps(self.DEFAULT_CONFIG))
        except Exception as e:
             print(f"Warning/Error loading config file: {e}. Using default values.")
             return json.loads(json.dumps(self.DEFAULT_CONFIG))

        config_data = json.loads(json.dumps(self.DEFAULT_CONFIG))
        for section, default_section_data in self.DEFAULT_CONFIG.items():
            loaded_section_data = loaded_data.get(section)
            config_section = config_data.setdefault(section, {})
            if isinstance(loaded_section_data, dict) and isinstance(config_section, dict):
                for key, default_value in default_section_data.items():
                    loaded_value = loaded_section_data.get(key, default_value)
                    if key in config_data.get("actions",{}) and isinstance(default_value, dict) and not isinstance(loaded_value, dict) and loaded_value is not None:
                         print(f"Warning: Incorrect type for action '{key}' in config file. Using default.")
                         config_section[key] = default_value
                    else:
                         config_section[key] = loaded_value
            elif section == "settings" and isinstance(loaded_section_data, dict):
                 for key, default_value in default_section_data.items():
                      config_section[key] = loaded_section_data.get(key, default_value)
            # Allow loading sections not in default? No, stick to defined structure.

        print("Configuration loaded and merged with defaults.")
        return config_data


    def _save_internal(self, data_to_save):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4)
            return True
        except Exception as e: print(f"Error saving configuration internally: {e}"); return False

    def save(self):
        self._sync_sections()
        if self._save_internal(self.config_data):
             print(f"Configuration successfully saved to {self.config_path}"); return True
        else: print(f"Error saving configuration to {self.config_path}"); return False

    def get_config(self): return self.config_data
    def get_thresholds(self): return self.config_data.get("thresholds", {})
    def get_actions(self): return self.config_data.get("actions", {})
    def get_enabled_gestures(self): return self.config_data.get("enabled_gestures", {})
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
        self.config_data["actions"] = new_actions_dict; print(f"Updating actions in config: {new_actions_dict}"); return self.save()
    def update_action(self, key, action_config):
         self.config_data.setdefault("actions", {})[key] = action_config; print(f"Updating action '{key}' in config: {action_config}"); return self.save()
    def update_gesture_enabled(self, key, is_enabled):
        self.config_data.setdefault("enabled_gestures", {})[key] = bool(is_enabled); print(f"Updating enabled status for '{key}' to {is_enabled}"); return self.save()
    def update_setting(self, key, value):
        self.config_data.setdefault("settings", {})[key] = value; print(f"Updating setting '{key}' in config to {value}"); return self.save()