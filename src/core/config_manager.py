import json
import os

class ConfigManager:
    """Handles loading, saving, and accessing configuration data from a JSON file."""

    DEFAULT_CONFIG = {
        "thresholds": {
            "mouth_open": 0.35,
            "eyebrows_raised": 0.28,
            "smile": 0.35
        },
        "actions": {
            "mouth_open": {"type": "press", "value": "a"},
            "eyebrows_raised": {"type": "press", "value": "enter"},
            "smile": {"type": "write", "value": ":\)"}
        }
    }

    def __init__(self, config_filename="config.json"):
        """
        Initializes the manager and loads the configuration.

        :param config_filename: Name of the configuration file. Assumed to be
                                in the parent directory of this script's location (project root).
        """
        script_dir = os.path.dirname(os.path.realpath(__file__))
        self.config_path = os.path.join(script_dir, "..", config_filename)
        self.config_data = self._load()
        print(f"ConfigManager initialized. Config path: {self.config_path}")

    def _load(self):
        """Loads configuration from the JSON file, using defaults if necessary."""
        print(f"Attempting to load configuration from: {self.config_path}")
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                config_data = self.DEFAULT_CONFIG.copy()
                for section, defaults in self.DEFAULT_CONFIG.items():
                    loaded_section = loaded_data.get(section, {})
                    config_section = config_data.setdefault(section, {})
                    for key, value in defaults.items():
                         config_section.setdefault(key, value)
                    config_section.update(loaded_section)

                print("Configuration loaded successfully.")
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
         """Internal save method to avoid issues during initial load/save."""
         try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4)
            return True
         except Exception as e:
            print(f"Error saving configuration internally: {e}")
            return False

    def save(self):
        """Saves the current configuration data back to the JSON file."""
        if self._save_internal(self.config_data):
             print(f"Configuration successfully saved to {self.config_path}")
             return True
        else:
             print(f"Error saving configuration to {self.config_path}")
             return False

    def get_config(self):
        """Returns the entire configuration dictionary."""
        return self.config_data

    def get_thresholds(self):
        """Returns the 'thresholds' dictionary."""
        return self.config_data.get("thresholds", {})

    def get_actions(self):
        """Returns the 'actions' dictionary."""
        return self.config_data.get("actions", {})

    def get_threshold(self, key, default=None):
        """Gets a specific threshold value."""
        default_value = self.DEFAULT_CONFIG.get("thresholds", {}).get(key, default)
        return self.get_thresholds().get(key, default_value)

    def get_action(self, key):
        """Gets a specific action configuration dictionary."""
        default_value = self.DEFAULT_CONFIG.get("actions", {}).get(key, None)
        return self.get_actions().get(key, default_value)

    def update_thresholds(self, new_thresholds_dict):
        """Updates the thresholds section and saves the config."""
        if "thresholds" not in self.config_data:
            self.config_data["thresholds"] = {}
        self.config_data["thresholds"].update(new_thresholds_dict)
        print(f"Updating thresholds in config: {new_thresholds_dict}")
        return self.save()

    def update_actions(self, new_actions_dict):
        """Replaces the actions section and saves the config."""
        self.config_data["actions"] = new_actions_dict
        print(f"Updating actions in config: {new_actions_dict}")
        return self.save()

    def update_action(self, key, action_config):
         """Updates a single action and saves the config."""
         if "actions" not in self.config_data:
             self.config_data["actions"] = {}
         self.config_data["actions"][key] = action_config
         print(f"Updating action '{key}' in config: {action_config}")
         return self.save()
