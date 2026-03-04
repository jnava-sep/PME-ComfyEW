from __future__ import annotations
import os
import sys
import json
import random
import re
import logging
import importlib.util
import traceback
from PIL import Image, ImageOps, ImageSequence
from PIL.PngImagePlugin import PngInfo
import numpy as np
import folder_paths
from comfy.cli_args import args
from comfy.comfy_types import IO

def before_node_execution():
    pass


def interrupt_processing(value=True):
    pass

class SaveImage:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "The images to save."}),
                "filename_prefix": ("STRING", {"default": "ComfyUI", "tooltip": "The prefix for the file to save. This may include formatting information such as %date:yyyy-MM-dd% or %Empty Latent Image.width% to include values from nodes."})
            },
            "hidden": {
                "prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "image"
    ESSENTIALS_CATEGORY = "Basics"
    DESCRIPTION = "Saves the input images to your ComfyUI output directory."
    SEARCH_ALIASES = ["save", "save image", "export image", "output image", "write image", "download"]

    def save_images(self, images, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None):
        filename_prefix += self.prefix_append
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0])
        results = list()
        for (batch_number, image) in enumerate(images):
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            metadata = None
            if not args.disable_metadata:
                metadata = PngInfo()
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            filename_with_batch_num = filename.replace("%batch_num%", str(batch_number))
            file = f"{filename_with_batch_num}_{counter:05}_.png"
            img.save(os.path.join(full_output_folder, file), pnginfo=metadata, compress_level=self.compress_level)
            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type
            })
            counter += 1

        return { "ui": { "images": results } }

class PreviewImage(SaveImage):
    def __init__(self):
        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"
        self.prefix_append = "_temp_" + ''.join(random.choice("abcdefghijklmnopqrstupvxyz") for x in range(5))
        self.compress_level = 1

    SEARCH_ALIASES = ["preview", "preview image", "show image", "view image", "display image", "image viewer"]

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"images": ("IMAGE", ), }, "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},}

class StringInput:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"value": ("STRING", {"default": "", "multiline": False, "tooltip": "The string value to output."})}}
    RETURN_TYPES = ("STRING",)
    FUNCTION = "produce"
    CATEGORY = "utils/string"
    def produce(self, value):
        return (value,)

class StringMultilineInput:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"value": ("STRING", {"default": "", "multiline": True, "tooltip": "Multiline string value."})}}
    RETURN_TYPES = ("STRING",)
    FUNCTION = "produce"
    CATEGORY = "utils/string"
    def produce(self, value):
        return (value,)

class IntInput:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"value": ("INT", {"default": 0, "min": -2147483648, "max": 2147483647, "tooltip": "Integer value."})}}
    RETURN_TYPES = ("INT",)
    FUNCTION = "produce"
    CATEGORY = "utils/number"
    def produce(self, value):
        return (value,)

class FloatInput:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"value": ("FLOAT", {"default": 0.0, "step": 0.01, "min": -1e9, "max": 1e9, "tooltip": "Floating point value."})}}
    RETURN_TYPES = ("FLOAT",)
    FUNCTION = "produce"
    CATEGORY = "utils/number"
    def produce(self, value):
        return (value,)

class BooleanInput:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"value": ("BOOLEAN", {"default": False, "tooltip": "Boolean value."})}}
    RETURN_TYPES = ("BOOLEAN",)
    FUNCTION = "produce"
    CATEGORY = "utils/logic"
    def produce(self, value):
        return (value,)

class StringConcatenateNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "string_a": ("STRING", {"multiline": True}),
            "string_b": ("STRING", {"multiline": True}),
            "delimiter": ("STRING", {"default": "", "tooltip": "Inserted between both strings."})}}
    RETURN_TYPES = ("STRING",)
    FUNCTION = "concat"
    CATEGORY = "utils/string"
    def concat(self, string_a, string_b, delimiter):
        return (delimiter.join((string_a, string_b)),)

class StringSubstringNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "string": ("STRING", {"multiline": True}),
            "start": ("INT", {"default": 0, "tooltip": "Start index."}),
            "end": ("INT", {"default": 0, "tooltip": "End index (0 = end of string)."}),
        }}
    RETURN_TYPES = ("STRING",)
    FUNCTION = "substring"
    CATEGORY = "utils/string"
    def substring(self, string, start, end):
        end_idx = None if end == 0 else end
        return (string[start:end_idx],)

class StringLengthNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"string": ("STRING", {"multiline": True})}}
    RETURN_TYPES = ("INT",)
    FUNCTION = "length"
    CATEGORY = "utils/string"
    def length(self, string):
        return (len(string),)

class StringCaseConverterNode:
    MODES = ["UPPERCASE", "lowercase", "Capitalize", "Title Case"]
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "string": ("STRING", {"multiline": True}),
            "mode": (cls.MODES,),
        }}
    RETURN_TYPES = ("STRING",)
    FUNCTION = "convert"
    CATEGORY = "utils/string"
    def convert(self, string, mode):
        mapping = {
            "UPPERCASE": string.upper,
            "lowercase": string.lower,
            "Capitalize": string.capitalize,
            "Title Case": string.title,
        }
        return (mapping.get(mode, lambda: string)(),)

class StringTrimNode:
    MODES = ["Both", "Left", "Right"]
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "string": ("STRING", {"multiline": True}),
            "mode": (cls.MODES,),
        }}
    RETURN_TYPES = ("STRING",)
    FUNCTION = "trim"
    CATEGORY = "utils/string"
    def trim(self, string, mode):
        if mode == "Left":
            return (string.lstrip(),)
        if mode == "Right":
            return (string.rstrip(),)
        return (string.strip(),)

class StringReplaceNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "string": ("STRING", {"multiline": True}),
            "find": ("STRING", {"multiline": True}),
            "replace": ("STRING", {"multiline": True}),
        }}
    RETURN_TYPES = ("STRING",)
    FUNCTION = "replace"
    CATEGORY = "utils/string"
    def replace(self, string, find, replace):
        return (string.replace(find, replace),)

class StringContainsNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "string": ("STRING", {"multiline": True}),
            "substring": ("STRING", {"multiline": True}),
            "case_sensitive": ("BOOLEAN", {"default": True, "advanced": True}),
        }}
    RETURN_TYPES = ("BOOLEAN",)
    FUNCTION = "contains"
    CATEGORY = "utils/string"
    def contains(self, string, substring, case_sensitive):
        if case_sensitive:
            return (substring in string,)
        return (substring.lower() in string.lower(),)

class StringCompareNode:
    MODES = ["Equal", "Starts With", "Ends With"]
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "string_a": ("STRING", {"multiline": True}),
            "string_b": ("STRING", {"multiline": True}),
            "mode": (cls.MODES,),
            "case_sensitive": ("BOOLEAN", {"default": True, "advanced": True}),
        }}
    RETURN_TYPES = ("BOOLEAN",)
    FUNCTION = "compare"
    CATEGORY = "utils/string"
    def compare(self, string_a, string_b, mode, case_sensitive):
        a = string_a if case_sensitive else string_a.lower()
        b = string_b if case_sensitive else string_b.lower()
        if mode == "Equal":
            return (a == b,)
        if mode == "Starts With":
            return (a.startswith(b),)
        if mode == "Ends With":
            return (a.endswith(b),)
        return (False,)

class StringRegexMatchNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "string": ("STRING", {"multiline": True}),
            "pattern": ("STRING", {"multiline": True}),
            "case_insensitive": ("BOOLEAN", {"default": True, "advanced": True}),
            "multiline": ("BOOLEAN", {"default": False, "advanced": True}),
            "dotall": ("BOOLEAN", {"default": False, "advanced": True}),
        }}
    RETURN_TYPES = ("BOOLEAN",)
    FUNCTION = "match"
    CATEGORY = "utils/string"
    def match(self, string, pattern, case_insensitive, multiline, dotall):
        flags = 0
        if case_insensitive:
            flags |= re.IGNORECASE
        if multiline:
            flags |= re.MULTILINE
        if dotall:
            flags |= re.DOTALL
        try:
            return (re.search(pattern, string, flags) is not None,)
        except re.error:
            return (False,)

class StringRegexExtractNode:
    MODES = ["First Match", "All Matches", "First Group", "All Groups"]
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "string": ("STRING", {"multiline": True}),
            "pattern": ("STRING", {"multiline": True}),
            "mode": (cls.MODES,),
            "case_insensitive": ("BOOLEAN", {"default": True, "advanced": True}),
            "multiline": ("BOOLEAN", {"default": False, "advanced": True}),
            "dotall": ("BOOLEAN", {"default": False, "advanced": True}),
            "group_index": ("INT", {"default": 1, "min": 0, "max": 100, "advanced": True}),
        }}
    RETURN_TYPES = ("STRING",)
    FUNCTION = "extract"
    CATEGORY = "utils/string"
    def extract(self, string, pattern, mode, case_insensitive, multiline, dotall, group_index):
        flags = 0
        if case_insensitive:
            flags |= re.IGNORECASE
        if multiline:
            flags |= re.MULTILINE
        if dotall:
            flags |= re.DOTALL
        try:
            if mode == "First Match":
                match = re.search(pattern, string, flags)
                return (match.group(0) if match else "",)
            if mode == "All Matches":
                matches = re.findall(pattern, string, flags)
                if not matches:
                    return ("",)
                if isinstance(matches[0], tuple):
                    return ("\n".join(m[0] for m in matches if m),)
                return ("\n".join(matches),)
            if mode == "First Group":
                match = re.search(pattern, string, flags)
                if match and len(match.groups()) >= group_index:
                    return (match.group(group_index),)
                return ("",)
            if mode == "All Groups":
                matches = re.finditer(pattern, string, flags)
                collected = [m.group(group_index) for m in matches if m.groups() and len(m.groups()) >= group_index]
                return ("\n".join(collected),)
        except re.error:
            return ("",)
        return ("",)

class StringRegexReplaceNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "string": ("STRING", {"multiline": True}),
            "pattern": ("STRING", {"multiline": True}),
            "replace": ("STRING", {"multiline": True}),
            "case_insensitive": ("BOOLEAN", {"default": True, "optional": True, "advanced": True}),
            "multiline": ("BOOLEAN", {"default": False, "optional": True, "advanced": True}),
            "dotall": ("BOOLEAN", {"default": False, "optional": True, "advanced": True}),
            "count": ("INT", {"default": 0, "min": 0, "advanced": True, "tooltip": "0 replaces all matches."}),
        }}
    RETURN_TYPES = ("STRING",)
    FUNCTION = "regex_replace"
    CATEGORY = "utils/string"
    def regex_replace(self, string, pattern, replace, case_insensitive, multiline, dotall, count):
        flags = 0
        if case_insensitive:
            flags |= re.IGNORECASE
        if multiline:
            flags |= re.MULTILINE
        if dotall:
            flags |= re.DOTALL
        try:
            return (re.sub(pattern, replace, string, count=count, flags=flags),)
        except re.error:
            return (string,)

class PreviewAny:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"source": (IO.ANY, {})}}
    RETURN_TYPES = ()
    FUNCTION = "display"
    OUTPUT_NODE = True
    CATEGORY = "utils"
    SEARCH_ALIASES = ["preview", "inspect", "debug", "print"]
    def display(self, source=None):
        value = "None"
        if isinstance(source, str):
            value = source
        elif isinstance(source, (int, float, bool)):
            value = str(source)
        elif source is not None:
            try:
                value = json.dumps(source, indent=4)
            except Exception:
                try:
                    value = str(source)
                except Exception:
                    value = "source exists, but could not be serialized."
        return {"ui": {"text": (value,)}}

NODE_CLASS_MAPPINGS = {
    "SaveImage": SaveImage,
    "PreviewImage": PreviewImage,
    "StringInput": StringInput,
    "StringMultilineInput": StringMultilineInput,
    "IntInput": IntInput,
    "FloatInput": FloatInput,
    "BooleanInput": BooleanInput,
    "StringConcatenate": StringConcatenateNode,
    "StringSubstring": StringSubstringNode,
    "StringLength": StringLengthNode,
    "StringCaseConverter": StringCaseConverterNode,
    "StringTrim": StringTrimNode,
    "StringReplace": StringReplaceNode,
    "StringContains": StringContainsNode,
    "StringCompare": StringCompareNode,
    "StringRegexMatch": StringRegexMatchNode,
    "StringRegexExtract": StringRegexExtractNode,
    "StringRegexReplace": StringRegexReplaceNode,
    "PreviewAny": PreviewAny,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveImage": "Save Image",
    "PreviewImage": "Preview Image",
    "StringInput": "String",
    "StringMultilineInput": "String (Multiline)",
    "IntInput": "Int",
    "FloatInput": "Float",
    "BooleanInput": "Boolean",
    "StringConcatenate": "String/Concatenate",
    "StringSubstring": "String/Substring",
    "StringLength": "String/Length",
    "StringCaseConverter": "String/Case Converter",
    "StringTrim": "String/Trim",
    "StringReplace": "String/Replace",
    "StringContains": "String/Contains",
    "StringCompare": "String/Compare",
    "StringRegexMatch": "String/Regex Match",
    "StringRegexExtract": "String/Regex Extract",
    "StringRegexReplace": "String/Regex Replace",
    "PreviewAny": "Preview (Any)",
}

LOADED_MODULE_DIRS = {}
EXTENSION_WEB_DIRS = {}


def _get_module_name(module_path: str) -> str:
    base = os.path.basename(module_path.rstrip(os.sep))
    if os.path.isfile(module_path):
        base = os.path.splitext(base)[0]
    # replace characters invalid in module names with underscores
    sanitized = re.sub(r"\W|^(?=\d)", "_", base)
    if not sanitized:
        sanitized = "custom_node"
    return sanitized


def _load_spec(module_path: str):
    if os.path.isdir(module_path):
        init_file = os.path.join(module_path, "__init__.py")
        if not os.path.isfile(init_file):
            return None
        return importlib.util.spec_from_file_location(_get_module_name(module_path), init_file)
    if module_path.endswith(".py"):
        return importlib.util.spec_from_file_location(_get_module_name(module_path), module_path)
    return None


def _register_node_module(module, module_dir: str, ignore: set[str]):
    if hasattr(module, "NODE_CLASS_MAPPINGS") and module.NODE_CLASS_MAPPINGS:
        for name, node_cls in module.NODE_CLASS_MAPPINGS.items():
            if name in ignore:
                continue
            NODE_CLASS_MAPPINGS[name] = node_cls
    if hasattr(module, "NODE_DISPLAY_NAME_MAPPINGS") and module.NODE_DISPLAY_NAME_MAPPINGS:
        NODE_DISPLAY_NAME_MAPPINGS.update(module.NODE_DISPLAY_NAME_MAPPINGS)
    if hasattr(module, "WEB_DIRECTORY") and module.WEB_DIRECTORY:
        web_dir = os.path.abspath(os.path.join(module_dir, module.WEB_DIRECTORY))
        if os.path.isdir(web_dir):
            EXTENSION_WEB_DIRS[_get_module_name(module_dir)] = web_dir


async def _load_custom_node(module_path: str, ignore: set[str]):
    spec = _load_spec(module_path)
    if spec is None:
        return False
    module = importlib.util.module_from_spec(spec)
    try:
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)  # type: ignore[attr-defined]
        LOADED_MODULE_DIRS[_get_module_name(module_path)] = os.path.abspath(os.path.dirname(spec.origin))
        _register_node_module(module, os.path.dirname(spec.origin), ignore)
        logging.info("Loaded custom node module: %s", module_path)
        return True
    except Exception:
        logging.warning("Failed to load custom node module: %s", module_path)
        logging.warning(traceback.format_exc())
        sys.modules.pop(spec.name, None)
        return False


def _iter_custom_modules(base_path: str):
    for entry in os.listdir(base_path):
        if entry == "__pycache__" or entry.endswith(".disabled"):
            continue
        path = os.path.join(base_path, entry)
        if os.path.isdir(path) or path.endswith(".py"):
            yield path


async def init_extra_nodes(init_custom_nodes=True, init_api_nodes=True):
    if not init_custom_nodes:
        logging.info("Skipping custom nodes initialization per settings.")
        return []

    custom_paths = folder_paths.get_folder_paths("custom_nodes")
    existing = set(NODE_CLASS_MAPPINGS.keys())
    for root in custom_paths:
        if not os.path.isdir(root):
            continue
        for module_path in _iter_custom_modules(root):
            await _load_custom_node(module_path, existing)
    return []
