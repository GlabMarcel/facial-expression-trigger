import pytest
import json
import os
from src.core.config_manager import ConfigManager

def test_init_no_config_file_creates_default(fs):
    project_root = "/project"
    src_core_dir = fs.create_dir(os.path.join(project_root, "src", "core"))
    config_path = os.path.join(project_root, "config.json")

    manager = ConfigManager(config_filename=config_path)

    assert manager.get_config() == ConfigManager.DEFAULT_CONFIG
    assert fs.exists(config_path)
    with open(config_path, 'r') as f:
        content_on_disk = json.load(f)
    assert content_on_disk == ConfigManager.DEFAULT_CONFIG

def test_init_loads_existing_valid_config(fs):
    project_root = "/project"
    src_core_dir = fs.create_dir(os.path.join(project_root, "src", "core"))
    config_path = os.path.join(project_root, "config.json")
    test_config_content = {
        "thresholds": {"mouth_open": 0.99, "eyebrows_raised": 0.11},
        "actions": {"mouth_open": {"type": "test", "value": "test_val"}},
    }
    fs.create_file(config_path, contents=json.dumps(test_config_content))

    manager = ConfigManager(config_filename=config_path)

    assert manager.get_threshold("mouth_open") == 0.99
    assert manager.get_threshold("eyebrows_raised") == 0.11
    assert manager.get_threshold("smile") == ConfigManager.DEFAULT_CONFIG["thresholds"]["smile"]
    assert manager.get_action("mouth_open") == {"type": "test", "value": "test_val"}
    assert manager.get_action("eyebrows_raised") == ConfigManager.DEFAULT_CONFIG["actions"]["eyebrows_raised"]
    assert manager.get_enabled_gestures() == ConfigManager.DEFAULT_CONFIG["enabled_gestures"]

def test_init_loads_invalid_json_uses_default(fs):
    project_root = "/project"
    src_core_dir = fs.create_dir(os.path.join(project_root, "src", "core"))
    config_path = os.path.join(project_root, "config.json")
    fs.create_file(config_path, contents='{\n  "thresholds": {\n    "mouth_open": 0.3,\n  }\n}')

    manager = ConfigManager(config_filename=config_path)

    assert manager.get_config() == ConfigManager.DEFAULT_CONFIG

def test_save_updates_file_content(fs):
    project_root = "/project"
    src_core_dir = fs.create_dir(os.path.join(project_root, "src", "core"))
    config_path = os.path.join(project_root, "config.json")
    manager = ConfigManager(config_filename=config_path)

    updated_thresholds = {"mouth_open": 0.88, "smile": 0.77}
    save_success = manager.update_thresholds(updated_thresholds)

    assert save_success == True
    assert manager.get_threshold("mouth_open") == 0.88
    assert manager.get_threshold("smile") == 0.77
    assert fs.exists(config_path)
    with open(config_path, 'r') as f:
        content_on_disk = json.load(f)
    assert content_on_disk["thresholds"]["mouth_open"] == 0.88
    assert content_on_disk["thresholds"]["smile"] == 0.77
    assert "actions" in content_on_disk

def test_update_action_saves_correctly(fs):
    project_root = "/project"
    src_core_dir = fs.create_dir(os.path.join(project_root, "src", "core"))
    config_path = os.path.join(project_root, "config.json")
    manager = ConfigManager(config_filename=config_path)
    new_action = {"type": "hotkey", "value": "win,d"}

    save_success = manager.update_action("eyebrows_raised", new_action)

    assert save_success == True
    assert manager.get_action("eyebrows_raised") == new_action
    with open(config_path, 'r') as f:
        content_on_disk = json.load(f)
    assert content_on_disk["actions"]["eyebrows_raised"] == new_action
    assert content_on_disk["actions"]["mouth_open"] == ConfigManager.DEFAULT_CONFIG["actions"]["mouth_open"]

def test_update_gesture_enabled_saves_correctly(fs):
    project_root = "/project"
    src_core_dir = fs.create_dir(os.path.join(project_root, "src", "core"))
    config_path = os.path.join(project_root, "config.json")
    manager = ConfigManager(config_filename=config_path)
    assert manager.get_enabled_gestures().get("smile") == True

    save_success = manager.update_gesture_enabled("smile", False)

    assert save_success == True
    assert manager.get_enabled_gestures().get("smile") == False
    with open(config_path, 'r') as f:
        content_on_disk = json.load(f)
    assert content_on_disk["enabled_gestures"]["smile"] == False
    assert content_on_disk["enabled_gestures"]["mouth_open"] == True

def test_load_partial_config_merges_defaults(fs):
    project_root = "/project"
    src_core_dir = fs.create_dir(os.path.join(project_root, "src", "core"))
    config_path = os.path.join(project_root, "config.json")
    test_config_content = {
        "thresholds": {"mouth_open": 0.1, "eyebrows_raised": 0.2, "smile": 0.3}
    }
    fs.create_file(config_path, contents=json.dumps(test_config_content))

    manager = ConfigManager(config_filename=config_path)

    assert manager.get_threshold("mouth_open") == 0.1
    assert manager.get_actions() == ConfigManager.DEFAULT_CONFIG["actions"]
    assert manager.get_enabled_gestures() == ConfigManager.DEFAULT_CONFIG["enabled_gestures"]

def test_getters_with_nonexistent_keys(fs):
    project_root = "/project"
    src_core_dir = fs.create_dir(os.path.join(project_root, "src", "core"))
    config_path = os.path.join(project_root, "config.json")
    manager = ConfigManager(config_filename=config_path)
    non_existent_key = "non_existent_gesture"

    assert manager.get_threshold(non_existent_key) is None
    assert manager.get_threshold(non_existent_key, default=999) == 999
    assert manager.get_action(non_existent_key) is None
    enabled_gestures = manager.get_enabled_gestures()
    assert non_existent_key not in enabled_gestures
    assert enabled_gestures.get(non_existent_key, "fallback") == "fallback"