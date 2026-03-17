from __future__ import annotations

import os
import folder_paths
import glob
from aiohttp import web
import json
import logging
from functools import lru_cache
from pathlib import Path

from utils.json_util import merge_json_recursive


# Extra locale files to load into main.json
EXTRA_LOCALE_FILES = [
    "nodeDefs.json",
    "commands.json",
    "settings.json",
]


def safe_load_json_file(file_path: str) -> dict:
    if not os.path.exists(file_path):
        return {}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logging.error(f"Error loading {file_path}")
        return {}


class CustomNodeManager:
    LOCAL_TEMPLATE_CONFIG_FILENAME = "template_library.json"

    @classmethod
    def _local_template_config_path(cls) -> str:
        return os.path.join(
            folder_paths.get_user_directory(),
            "default",
            cls.LOCAL_TEMPLATE_CONFIG_FILENAME,
        )

    @classmethod
    def _load_local_template_config(cls) -> dict:
        config_path = cls._local_template_config_path()
        if not os.path.exists(config_path):
            return {}
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            return cfg if isinstance(cfg, dict) else {}
        except Exception as exc:
            logging.warning("Failed to load local template library config '%s': %s", config_path, exc)
            return {}

    @classmethod
    def _discover_local_template_categories(cls, user_root: str) -> list[tuple[str, str, list[str]]]:
        cfg = cls._load_local_template_config()
        library_root = Path(cfg.get("library_root") or os.path.join(user_root, "default", "template_library"))
        categories_cfg = cfg.get("categories")
        categories: list[tuple[str, str, list[str]]] = []

        if isinstance(categories_cfg, list):
            for entry in categories_cfg:
                if not isinstance(entry, dict):
                    continue
                name = str(entry.get("name") or "").strip()
                if not name:
                    continue
                rel = str(entry.get("path") or name).strip()
                category_dir = (library_root / rel).resolve()
                if not category_dir.exists() or not category_dir.is_dir():
                    continue
                workflows = sorted(p.stem for p in category_dir.glob("*.json"))
                categories.append((name, str(category_dir), workflows))
            return categories

        if not library_root.exists() or not library_root.is_dir():
            return categories

        for category_dir in sorted(p for p in library_root.iterdir() if p.is_dir()):
            workflows = sorted(p.stem for p in category_dir.glob("*.json"))
            categories.append((category_dir.name, str(category_dir), workflows))
        return categories

    @lru_cache(maxsize=1)
    def build_translations(self):
        """Load all custom nodes translations during initialization. Translations are
        expected to be loaded from `locales/` folder.

        The folder structure is expected to be the following:
        - custom_nodes/
            - custom_node_1/
                - locales/
                    - en/
                        - main.json
                        - commands.json
                        - settings.json

        returned translations are expected to be in the following format:
        {
            "en": {
                "nodeDefs": {...},
                "commands": {...},
                "settings": {...},
                ...{other main.json keys}
            }
        }
        """

        translations = {}

        for folder in folder_paths.get_folder_paths("custom_nodes"):
            # Sort glob results for deterministic ordering
            for custom_node_dir in sorted(glob.glob(os.path.join(folder, "*/"))):
                locales_dir = os.path.join(custom_node_dir, "locales")
                if not os.path.exists(locales_dir):
                    continue

                for lang_dir in glob.glob(os.path.join(locales_dir, "*/")):
                    lang_code = os.path.basename(os.path.dirname(lang_dir))

                    if lang_code not in translations:
                        translations[lang_code] = {}

                    # Load main.json
                    main_file = os.path.join(lang_dir, "main.json")
                    node_translations = safe_load_json_file(main_file)

                    # Load extra locale files
                    for extra_file in EXTRA_LOCALE_FILES:
                        extra_file_path = os.path.join(lang_dir, extra_file)
                        key = extra_file.split(".")[0]
                        json_data = safe_load_json_file(extra_file_path)
                        if json_data:
                            node_translations[key] = json_data

                    if node_translations:
                        translations[lang_code] = merge_json_recursive(
                            translations[lang_code], node_translations
                        )

        return translations

    def add_routes(self, routes, webapp, loadedModules):

        example_workflow_folder_names = ["example_workflows", "example", "examples", "workflow", "workflows"]
        local_template_cfg = self._load_local_template_config()
        hide_auto_examples = bool(local_template_cfg.get("hide_auto_discovered_examples", False))
        local_categories = self._discover_local_template_categories(folder_paths.get_user_directory())
        for display_name, category_dir, _ in local_categories:
            if "/" in display_name or "\\" in display_name:
                logging.warning("Skipping local template category with invalid name '%s'", display_name)
                continue
            if os.path.isdir(category_dir):
                webapp.add_routes(
                    [
                        web.static(
                            "/api/workflow_templates/" + display_name,
                            category_dir,
                        )
                    ]
                )

        @routes.get("/workflow_templates")
        async def get_workflow_templates(request):
            """Returns a web response that contains the map of custom_nodes names and their associated workflow templates. The ones without templates are omitted."""

            workflow_templates_dict = {}

            for display_name, _, workflows in local_categories:
                workflow_templates_dict[display_name] = workflows

            if hide_auto_examples:
                return web.json_response(workflow_templates_dict)

            files = []

            for folder in folder_paths.get_folder_paths("custom_nodes"):
                for folder_name in example_workflow_folder_names:
                    pattern = os.path.join(folder, f"*/{folder_name}/*.json")
                    matched_files = glob.glob(pattern)
                    files.extend(matched_files)

            # custom_nodes folder name -> example workflow names
            for file in files:
                custom_nodes_name = os.path.basename(
                    os.path.dirname(os.path.dirname(file))
                )
                workflow_name = os.path.splitext(os.path.basename(file))[0]
                workflow_templates_dict.setdefault(custom_nodes_name, []).append(
                    workflow_name
                )
            return web.json_response(workflow_templates_dict)

        # Serve workflow templates from custom nodes.
        for module_name, module_dir in loadedModules:
            for folder_name in example_workflow_folder_names:
                workflows_dir = os.path.join(module_dir, folder_name)

                if os.path.exists(workflows_dir):
                    if folder_name != "example_workflows":
                        logging.debug(
                            "Found example workflow folder '%s' for custom node '%s', consider renaming it to 'example_workflows'",
                            folder_name, module_name)

                    webapp.add_routes(
                        [
                            web.static(
                                "/api/workflow_templates/" + module_name, workflows_dir
                            )
                        ]
                    )

        @routes.get("/i18n")
        async def get_i18n(request):
            """Returns translations from all custom nodes' locales folders."""
            return web.json_response(self.build_translations())
