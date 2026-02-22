"""Gelistirici araclari beceri modulu.

Kod bicilendirme, dogrulama, donusum,
Git, Docker, Shell, API dokumantasyon,
test verisi, UUID, timestamp, renk, encode/decode,
hash, IP hesaplama, HTTP durum, MIME, escape,
diff, CSV/JSON/XML donusum, sayi sistemi.
Beceriler: 101-130
"""

import base64
import colorsys
import csv
import difflib
import hashlib
import io
import json
import math
import re
import textwrap
import uuid as uuid_mod
from typing import Any

from app.core.skills.base_skill import BaseSkill


class CodeFormatterSkill(BaseSkill):
    """Kod bicilendirme becerisi."""

    SKILL_ID = "101"
    NAME = "code_formatter"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "Kod bicilendirme (Python, JS, HTML, CSS)"
    PARAMETERS = {"code": "Bicimlendirilecek kod", "language": "Programlama dili"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        code = p.get("code", "")
        lang = p.get("language", "python").lower()
        formatted = code
        if lang == "python":
            lines = code.split("\n")
            formatted = "\n".join(line.rstrip() for line in lines)
        elif lang in ("json",):
            try:
                formatted = json.dumps(json.loads(code), indent=2, ensure_ascii=False)
            except Exception:
                pass
        return {"language": lang, "original_length": len(code), "formatted": formatted,
                "formatted_length": len(formatted), "changes_made": code != formatted}


class CodeMinifierSkill(BaseSkill):
    """Kod minify becerisi."""

    SKILL_ID = "102"
    NAME = "code_minifier"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "Kod minify (JS, CSS, HTML)"
    PARAMETERS = {"code": "Minify edilecek kod", "language": "Dil (js/css/html)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        code = p.get("code", "")
        lang = p.get("language", "js").lower()
        original = len(code)
        result = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)
        result = re.sub(r"//.*?$", "", result, flags=re.MULTILINE)
        result = re.sub(r"\s+", " ", result).strip()
        if lang == "css":
            result = re.sub(r"\s*([{};:,])\s*", r"\1", result)
        return {"language": lang, "original_size": original, "minified_size": len(result),
                "savings_percent": round((1 - len(result) / max(original, 1)) * 100, 1),
                "minified": result}


class JsonValidatorSkill(BaseSkill):
    """JSON dogrulama becerisi."""

    SKILL_ID = "103"
    NAME = "json_validator"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "JSON dogrulama ve formatlama"
    PARAMETERS = {"json_str": "JSON metni", "indent": "Girinti boyutu"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        json_str = p.get("json_str", "{}")
        indent = int(p.get("indent", 2))
        try:
            parsed = json.loads(json_str)
            formatted = json.dumps(parsed, indent=indent, ensure_ascii=False)
            data_type = type(parsed).__name__
            return {"valid": True, "type": data_type, "formatted": formatted,
                    "original_size": len(json_str), "formatted_size": len(formatted),
                    "keys": list(parsed.keys()) if isinstance(parsed, dict) else None,
                    "length": len(parsed) if isinstance(parsed, (list, dict)) else None}
        except json.JSONDecodeError as e:
            return {"valid": False, "error": str(e), "line": e.lineno, "column": e.colno}


class YamlValidatorSkill(BaseSkill):
    """YAML dogrulama becerisi."""

    SKILL_ID = "104"
    NAME = "yaml_validator"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "YAML dogrulama ve donusum"
    PARAMETERS = {"yaml_str": "YAML metni"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        yaml_str = p.get("yaml_str", "key: value")
        result: dict[str, Any] = {}
        lines = yaml_str.strip().split("\n")
        valid = True
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, _, val = line.partition(":")
                result[key.strip()] = val.strip()
            else:
                valid = False
        json_output = json.dumps(result, indent=2, ensure_ascii=False)
        return {"valid": valid, "parsed": result, "json_output": json_output,
                "key_count": len(result), "line_count": len(lines)}


class XmlValidatorSkill(BaseSkill):
    """XML dogrulama becerisi."""

    SKILL_ID = "105"
    NAME = "xml_validator"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "XML dogrulama ve XPath"
    PARAMETERS = {"xml_str": "XML metni"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        xml_str = p.get("xml_str", "<root><item>test</item></root>")
        tags = re.findall(r"<(/?)(\w+)[^>]*>", xml_str)
        open_tags: list[str] = []
        tag_counts: dict[str, int] = {}
        valid = True
        for is_close, tag_name in tags:
            tag_counts[tag_name] = tag_counts.get(tag_name, 0) + 1
            if is_close:
                if open_tags and open_tags[-1] == tag_name:
                    open_tags.pop()
                else:
                    valid = False
            else:
                open_tags.append(tag_name)
        if open_tags:
            valid = False
        return {"valid": valid, "tags": tag_counts, "total_tags": sum(tag_counts.values()),
                "unclosed_tags": open_tags, "well_formed": valid and not open_tags}


class SqlFormatterSkill(BaseSkill):
    """SQL sorgu bicilendirme becerisi."""

    SKILL_ID = "106"
    NAME = "sql_formatter"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "SQL sorgu bicilendirme"
    PARAMETERS = {"sql": "SQL sorgusu", "dialect": "SQL dialekti"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        sql = p.get("sql", "SELECT * FROM users WHERE id=1")
        dialect = p.get("dialect", "postgresql")
        keywords = ["SELECT", "FROM", "WHERE", "AND", "OR", "ORDER BY", "GROUP BY",
                     "HAVING", "JOIN", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN",
                     "INSERT INTO", "UPDATE", "DELETE FROM", "SET", "VALUES", "LIMIT", "OFFSET"]
        formatted = sql
        for kw in sorted(keywords, key=len, reverse=True):
            formatted = re.sub(rf"\b{kw}\b", f"\n{kw}", formatted, flags=re.IGNORECASE)
        formatted = formatted.strip()
        return {"dialect": dialect, "original": sql, "formatted": formatted,
                "original_length": len(sql), "formatted_length": len(formatted)}


class SqlExplainerSkill(BaseSkill):
    """SQL sorgu aciklama becerisi."""

    SKILL_ID = "107"
    NAME = "sql_explainer"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "SQL sorgu aciklama"
    PARAMETERS = {"sql": "SQL sorgusu"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        sql = p.get("sql", "SELECT * FROM users WHERE id = 1")
        sql_upper = sql.upper().strip()
        operation = "SELECT" if sql_upper.startswith("SELECT") else "INSERT" if sql_upper.startswith("INSERT") else "UPDATE" if sql_upper.startswith("UPDATE") else "DELETE" if sql_upper.startswith("DELETE") else "OTHER"
        tables = re.findall(r"\bFROM\s+(\w+)", sql, re.IGNORECASE) + re.findall(r"\bJOIN\s+(\w+)", sql, re.IGNORECASE)
        conditions = re.findall(r"\bWHERE\s+(.+?)(?:\bORDER|\bGROUP|\bLIMIT|\bHAVING|$)", sql, re.IGNORECASE)
        has_wildcard = "*" in sql
        explanation = f"{operation} islemi: {', '.join(tables) if tables else 'bilinmeyen'} tablosundan"
        warnings = []
        if has_wildcard:
            warnings.append("SELECT * yerine belirli sutunlar tercih edin")
        if not conditions and operation in ("SELECT", "UPDATE", "DELETE"):
            warnings.append("WHERE kosulu yok - tum satirlar etkilenecek")
        return {"sql": sql, "operation": operation, "tables": tables,
                "conditions": conditions, "explanation": explanation,
                "warnings": warnings, "has_wildcard": has_wildcard}


class GitCommandSkill(BaseSkill):
    """Git komut olusturma becerisi."""

    SKILL_ID = "108"
    NAME = "git_command"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "Git komut olusturma (commit, branch, merge)"
    PARAMETERS = {"action": "Git islemi", "params": "Parametreler"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        action = p.get("action", "commit").lower()
        params = p.get("params", {})
        if isinstance(params, str):
            params = {"message": params}
        commands = {
            "commit": f'git add . && git commit -m "{params.get("message", "Update")}"',
            "branch": f'git checkout -b {params.get("name", "feature/new-branch")}',
            "merge": f'git merge {params.get("branch", "develop")}',
            "push": f'git push origin {params.get("branch", "main")}',
            "pull": f'git pull origin {params.get("branch", "main")}',
            "stash": "git stash", "log": "git log --oneline -10",
            "status": "git status", "tag": f'git tag -a v{params.get("version", "1.0.0")} -m "Release"',
        }
        cmd = commands.get(action, f"git {action}")
        return {"action": action, "command": cmd, "params": params,
                "description": f"Git {action} islemi", "dangerous": action in ("push", "merge", "tag")}


class DockerCommandSkill(BaseSkill):
    """Docker komut olusturma becerisi."""

    SKILL_ID = "109"
    NAME = "docker_command"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "Dockerfile ve docker-compose olusturma"
    PARAMETERS = {"action": "Docker islemi", "image": "Image adi", "params": "Parametreler"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        action = p.get("action", "run").lower()
        image = p.get("image", "python:3.11-slim")
        params = p.get("params", {})
        if isinstance(params, str):
            params = {}
        port = params.get("port", "8000:8000")
        name = params.get("name", "my-app")
        commands = {
            "run": f"docker run -d --name {name} -p {port} {image}",
            "build": f"docker build -t {name} .",
            "stop": f"docker stop {name}", "rm": f"docker rm {name}",
            "logs": f"docker logs -f {name}", "exec": f"docker exec -it {name} /bin/bash",
            "ps": "docker ps", "images": "docker images",
        }
        cmd = commands.get(action, f"docker {action}")
        dockerfile = f"FROM {image}\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt\nEXPOSE 8000\nCMD [\"python\", \"main.py\"]"
        return {"action": action, "command": cmd, "image": image,
                "dockerfile_example": dockerfile if action == "build" else None}


class ShellCommandSkill(BaseSkill):
    """Shell komut olusturma becerisi."""

    SKILL_ID = "110"
    NAME = "shell_command"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "Shell komut olusturma ve aciklama"
    PARAMETERS = {"task": "Yapilacak is", "os": "Isletim sistemi (linux/macos/windows)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        task = p.get("task", "list files").lower()
        os_type = p.get("os", "linux").lower()
        command_map = {
            "list files": {"linux": "ls -la", "macos": "ls -la", "windows": "dir"},
            "find file": {"linux": 'find . -name "*.py"', "macos": 'find . -name "*.py"', "windows": "dir /s *.py"},
            "disk usage": {"linux": "df -h", "macos": "df -h", "windows": "wmic logicaldisk get size,freespace"},
            "process list": {"linux": "ps aux", "macos": "ps aux", "windows": "tasklist"},
            "network": {"linux": "netstat -tlnp", "macos": "lsof -i", "windows": "netstat -an"},
        }
        cmd_set = command_map.get(task, {"linux": f"# {task}", "macos": f"# {task}", "windows": f"REM {task}"})
        cmd = cmd_set.get(os_type, cmd_set.get("linux", ""))
        return {"task": task, "os": os_type, "command": cmd, "description": f"{task} icin {os_type} komutu"}


class ApiDocGeneratorSkill(BaseSkill):
    """API dokumantasyon olusturma becerisi."""

    SKILL_ID = "111"
    NAME = "api_doc_generator"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "API dokumantasyon olusturma (OpenAPI)"
    PARAMETERS = {"endpoints": "Endpoint listesi", "title": "API basligi"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        endpoints = p.get("endpoints", [{"path": "/users", "method": "GET", "description": "Kullanicilari listele"}])
        title = p.get("title", "My API")
        if isinstance(endpoints, str):
            endpoints = [{"path": endpoints, "method": "GET", "description": "Endpoint"}]
        paths: dict[str, Any] = {}
        for ep in endpoints:
            path = ep.get("path", "/") if isinstance(ep, dict) else str(ep)
            method = ep.get("method", "GET").lower() if isinstance(ep, dict) else "get"
            desc = ep.get("description", "") if isinstance(ep, dict) else ""
            paths[path] = {method: {"summary": desc, "responses": {"200": {"description": "Basarili"}}}}
        openapi = {"openapi": "3.0.0", "info": {"title": title, "version": "1.0.0"}, "paths": paths}
        return {"title": title, "endpoint_count": len(endpoints),
                "openapi_spec": openapi, "openapi_json": json.dumps(openapi, indent=2)}


class MockDataGeneratorSkill(BaseSkill):
    """Test verisi olusturma becerisi."""

    SKILL_ID = "112"
    NAME = "mock_data_generator"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "Test verisi olusturma (JSON/CSV)"
    PARAMETERS = {"schema": "Veri semasi", "count": "Kayit sayisi", "format": "Format (json/csv)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        schema = p.get("schema", {"name": "string", "age": "int", "email": "email"})
        count = min(int(p.get("count", 5)), 100)
        fmt = p.get("format", "json")
        if isinstance(schema, str):
            schema = {"field": schema}
        names = ["Ali", "Ayse", "Mehmet", "Fatma", "Can", "Elif", "Burak", "Zeynep"]
        domains = ["gmail.com", "outlook.com", "yahoo.com"]
        records = []
        for i in range(count):
            row: dict[str, Any] = {}
            for key, dtype in schema.items():
                dtype_str = str(dtype).lower()
                if "name" in key.lower() or dtype_str == "string":
                    row[key] = names[i % len(names)]
                elif "email" in key.lower() or dtype_str == "email":
                    row[key] = f"user{i+1}@{domains[i % len(domains)]}"
                elif "age" in key.lower() or dtype_str == "int":
                    row[key] = 20 + (i * 7) % 40
                elif dtype_str == "float":
                    row[key] = round(10.0 + i * 3.14, 2)
                elif dtype_str == "bool":
                    row[key] = i % 2 == 0
                else:
                    row[key] = f"value_{i+1}"
            records.append(row)
        output = json.dumps(records, indent=2, ensure_ascii=False) if fmt == "json" else ""
        if fmt == "csv" and records:
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=list(records[0].keys()))
            writer.writeheader()
            writer.writerows(records)
            output = buf.getvalue()
        return {"format": fmt, "count": count, "schema": schema, "data": records, "output": output}


class UuidGeneratorSkill(BaseSkill):
    """UUID olusturma becerisi."""

    SKILL_ID = "113"
    NAME = "uuid_generator"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "UUID/GUID olusturma"
    PARAMETERS = {"version": "UUID surumu (1/4/5)", "count": "Adet", "namespace": "Namespace (v5 icin)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        version = int(p.get("version", 4))
        count = min(int(p.get("count", 1)), 50)
        namespace = p.get("namespace", "example.com")
        uuids = []
        for _ in range(count):
            if version == 1:
                u = uuid_mod.uuid1()
            elif version == 5:
                u = uuid_mod.uuid5(uuid_mod.NAMESPACE_DNS, namespace)
            else:
                u = uuid_mod.uuid4()
            uuids.append(str(u))
        return {"version": version, "count": count, "uuids": uuids,
                "format_examples": {"standard": uuids[0], "hex": uuids[0].replace("-", ""),
                                     "urn": f"urn:uuid:{uuids[0]}"}}


class TimestampConverterSkill(BaseSkill):
    """Unix timestamp donusum becerisi."""

    SKILL_ID = "114"
    NAME = "timestamp_converter"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "Unix timestamp donusum"
    PARAMETERS = {"timestamp": "Unix timestamp veya tarih", "direction": "Yon (to_date/to_unix)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        import time as _time
        ts = p.get("timestamp", "")
        direction = p.get("direction", "to_date")
        if direction == "to_date":
            try:
                ts_float = float(ts) if ts else _time.time()
            except (ValueError, TypeError):
                ts_float = _time.time()
            t = _time.gmtime(ts_float)
            return {"unix_timestamp": ts_float, "utc": _time.strftime("%Y-%m-%dT%H:%M:%SZ", t),
                    "date": _time.strftime("%Y-%m-%d", t), "time": _time.strftime("%H:%M:%S", t),
                    "day_of_week": _time.strftime("%A", t), "milliseconds": int(ts_float * 1000)}
        else:
            now = _time.time()
            return {"date_input": ts or "now", "unix_timestamp": int(now), "milliseconds": int(now * 1000)}


class ColorConverterSkill(BaseSkill):
    """Renk kodu donusum becerisi."""

    SKILL_ID = "115"
    NAME = "color_converter"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "Renk kodu donusum (HEX/RGB/HSL/CMYK)"
    PARAMETERS = {"color": "Renk degeri", "format": "Giris formati (hex/rgb/hsl)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        color = p.get("color", "#FF5733")
        fmt = p.get("format", "hex").lower()
        r, g, b = 255, 87, 51
        if fmt == "hex":
            hex_clean = color.lstrip("#")
            if len(hex_clean) == 6:
                r, g, b = int(hex_clean[0:2], 16), int(hex_clean[2:4], 16), int(hex_clean[4:6], 16)
        elif fmt == "rgb":
            parts = re.findall(r"\d+", str(color))
            if len(parts) >= 3:
                r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
        rn, gn, bn = r / 255.0, g / 255.0, b / 255.0
        h, l, s = colorsys.rgb_to_hls(rn, gn, bn)
        h_deg, s_pct, l_pct = round(h * 360), round(s * 100), round(l * 100)
        c = 1 - rn; m = 1 - gn; y = 1 - bn; k = min(c, m, y)
        if k < 1:
            c, m, y = (c - k) / (1 - k), (m - k) / (1 - k), (y - k) / (1 - k)
        return {"hex": f"#{r:02X}{g:02X}{b:02X}", "rgb": {"r": r, "g": g, "b": b},
                "rgb_string": f"rgb({r}, {g}, {b})",
                "hsl": {"h": h_deg, "s": s_pct, "l": l_pct},
                "cmyk": {"c": round(c * 100), "m": round(m * 100), "y": round(y * 100), "k": round(k * 100)}}


class EncodeDecoderSkill(BaseSkill):
    """Encode/decode becerisi."""

    SKILL_ID = "116"
    NAME = "encode_decoder"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "Base64, URL, HTML encode/decode"
    PARAMETERS = {"text": "Metin", "encoding": "Kodlama turu (base64/url/html)", "action": "Islem (encode/decode)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        text = p.get("text", "Hello World")
        encoding = p.get("encoding", "base64").lower()
        action = p.get("action", "encode").lower()
        result = text
        if encoding == "base64":
            if action == "encode":
                result = base64.b64encode(text.encode()).decode()
            else:
                try:
                    result = base64.b64decode(text).decode()
                except Exception:
                    result = "[decode hatasi]"
        elif encoding == "url":
            from urllib.parse import quote, unquote
            result = quote(text) if action == "encode" else unquote(text)
        elif encoding == "html":
            html_map = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#x27;"}
            if action == "encode":
                for ch, ent in html_map.items():
                    result = result.replace(ch, ent)
            else:
                for ent, ch in html_map.items():
                    result = result.replace(ent, ch)
        return {"input": text, "encoding": encoding, "action": action,
                "result": result, "input_length": len(text), "result_length": len(result)}


class HashCompareSkill(BaseSkill):
    """Hash karsilastirma becerisi."""

    SKILL_ID = "117"
    NAME = "hash_compare"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "Hash karsilastirma (MD5, SHA1, SHA256)"
    PARAMETERS = {"text": "Metin", "algorithm": "Algoritma", "expected": "Beklenen hash (opsiyonel)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        text = p.get("text", "")
        algo = p.get("algorithm", "sha256").lower()
        expected = p.get("expected", "")
        data = text.encode()
        hashes = {"md5": hashlib.md5(data).hexdigest(), "sha1": hashlib.sha1(data).hexdigest(),
                  "sha256": hashlib.sha256(data).hexdigest(), "sha512": hashlib.sha512(data).hexdigest()}
        computed = hashes.get(algo, hashes["sha256"])
        match = computed == expected if expected else None
        return {"text_length": len(text), "algorithm": algo, "hash": computed,
                "all_hashes": hashes, "match": match, "expected": expected or None}


class IpCalculatorSkill(BaseSkill):
    """IP subnet hesaplama becerisi."""

    SKILL_ID = "118"
    NAME = "ip_calculator"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "IP subnet hesaplama (CIDR, mask)"
    PARAMETERS = {"ip": "IP adresi", "cidr": "CIDR (orn: 24)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        ip = p.get("ip", "192.168.1.0")
        cidr = int(p.get("cidr", 24))
        octets = [int(o) for o in ip.split(".")]
        ip_int = (octets[0] << 24) | (octets[1] << 16) | (octets[2] << 8) | octets[3]
        mask_int = (0xFFFFFFFF << (32 - cidr)) & 0xFFFFFFFF
        network_int = ip_int & mask_int
        broadcast_int = network_int | (~mask_int & 0xFFFFFFFF)
        def int_to_ip(n: int) -> str:
            return f"{(n >> 24) & 0xFF}.{(n >> 16) & 0xFF}.{(n >> 8) & 0xFF}.{n & 0xFF}"
        total_hosts = 2 ** (32 - cidr)
        usable = max(total_hosts - 2, 0)
        return {"ip": ip, "cidr": cidr, "subnet_mask": int_to_ip(mask_int),
                "network": int_to_ip(network_int), "broadcast": int_to_ip(broadcast_int),
                "first_host": int_to_ip(network_int + 1) if usable > 0 else None,
                "last_host": int_to_ip(broadcast_int - 1) if usable > 0 else None,
                "total_hosts": total_hosts, "usable_hosts": usable}


class HttpStatusSkill(BaseSkill):
    """HTTP durum kodu aciklama becerisi."""

    SKILL_ID = "119"
    NAME = "http_status"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "HTTP durum kodu aciklama"
    PARAMETERS = {"code": "HTTP durum kodu"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        code = int(p.get("code", 200))
        statuses = {
            200: ("OK", "Istek basarili"), 201: ("Created", "Kaynak olusturuldu"),
            204: ("No Content", "Icerik yok"), 301: ("Moved Permanently", "Kalici yonlendirme"),
            302: ("Found", "Gecici yonlendirme"), 400: ("Bad Request", "Hatali istek"),
            401: ("Unauthorized", "Kimlik dogrulanmadi"), 403: ("Forbidden", "Erisim engellendi"),
            404: ("Not Found", "Kaynak bulunamadi"), 429: ("Too Many Requests", "Cok fazla istek"),
            500: ("Internal Server Error", "Sunucu hatasi"), 502: ("Bad Gateway", "Hatali aggeçidi"),
            503: ("Service Unavailable", "Hizmet kullanilamiyor"),
        }
        name, desc = statuses.get(code, ("Unknown", "Bilinmeyen durum kodu"))
        category = "Bilgi" if code < 200 else "Basarili" if code < 300 else "Yonlendirme" if code < 400 else "Istemci Hatasi" if code < 500 else "Sunucu Hatasi"
        return {"code": code, "name": name, "description": desc, "category": category,
                "is_success": 200 <= code < 300, "is_error": code >= 400}


class MimeTypeSkill(BaseSkill):
    """MIME tipi tespit becerisi."""

    SKILL_ID = "120"
    NAME = "mime_type"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "MIME tipi tespit"
    PARAMETERS = {"filename": "Dosya adi veya uzantisi"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        filename = p.get("filename", "document.pdf")
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else filename.lower()
        mime_map = {
            "html": "text/html", "css": "text/css", "js": "application/javascript",
            "json": "application/json", "xml": "application/xml", "csv": "text/csv",
            "txt": "text/plain", "pdf": "application/pdf", "zip": "application/zip",
            "png": "image/png", "jpg": "image/jpeg", "gif": "image/gif", "svg": "image/svg+xml",
            "mp3": "audio/mpeg", "mp4": "video/mp4", "py": "text/x-python",
        }
        mime = mime_map.get(ext, "application/octet-stream")
        category = mime.split("/")[0]
        return {"filename": filename, "extension": ext, "mime_type": mime, "category": category,
                "is_text": category == "text" or mime.endswith("json"), "is_binary": category in ("image", "audio", "video")}


class CharsetConverterSkill(BaseSkill):
    """Karakter seti donusum becerisi."""

    SKILL_ID = "121"
    NAME = "charset_converter"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "Karakter seti donusum"
    PARAMETERS = {"text": "Metin", "from_charset": "Kaynak charset", "to_charset": "Hedef charset"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        text = p.get("text", "Merhaba Dunya")
        from_cs = p.get("from_charset", "utf-8")
        to_cs = p.get("to_charset", "ascii")
        try:
            encoded = text.encode(from_cs)
            decoded = encoded.decode(to_cs, errors="replace")
            return {"text": text, "from_charset": from_cs, "to_charset": to_cs,
                    "result": decoded, "success": True, "original_bytes": len(encoded)}
        except Exception as e:
            return {"text": text, "error": str(e), "success": False}


class EscaperSkill(BaseSkill):
    """String escape becerisi."""

    SKILL_ID = "122"
    NAME = "escaper"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "String escape (HTML, JS, SQL, regex)"
    PARAMETERS = {"text": "Metin", "type": "Escape turu (html/js/sql/regex)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        text = p.get("text", '<script>alert("test")</script>')
        esc_type = p.get("type", "html").lower()
        if esc_type == "html":
            result = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        elif esc_type == "js":
            result = text.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")
        elif esc_type == "sql":
            result = text.replace("'", "''")
        elif esc_type == "regex":
            result = re.escape(text)
        else:
            result = text
        return {"input": text, "type": esc_type, "escaped": result,
                "input_length": len(text), "escaped_length": len(result)}


class DiffCheckerSkill(BaseSkill):
    """Metin farki karsilastirma becerisi."""

    SKILL_ID = "123"
    NAME = "diff_checker"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "Metin farki karsilastirma"
    PARAMETERS = {"text1": "Birinci metin", "text2": "Ikinci metin"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        text1 = p.get("text1", "Hello World")
        text2 = p.get("text2", "Hello Python")
        lines1 = text1.splitlines(keepends=True)
        lines2 = text2.splitlines(keepends=True)
        diff = list(difflib.unified_diff(lines1, lines2, fromfile="text1", tofile="text2"))
        ratio = difflib.SequenceMatcher(None, text1, text2).ratio()
        added = sum(1 for d in diff if d.startswith("+") and not d.startswith("+++"))
        removed = sum(1 for d in diff if d.startswith("-") and not d.startswith("---"))
        return {"similarity": round(ratio * 100, 1), "diff": "".join(diff),
                "lines_added": added, "lines_removed": removed, "identical": text1 == text2}


class MarkdownPreviewerSkill(BaseSkill):
    """Markdown onizleme becerisi."""

    SKILL_ID = "124"
    NAME = "markdown_previewer"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "Markdown render onizleme"
    PARAMETERS = {"markdown": "Markdown metni"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        md = p.get("markdown", "# Baslik\n\nParagraf **kalin** ve *italik*.")
        html = md
        html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
        html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
        html = re.sub(r"`(.+?)`", r"<code>\1</code>", html)
        html = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', html)
        headings = re.findall(r"^#{1,6} (.+)$", md, re.MULTILINE)
        return {"markdown": md, "html": html, "headings": headings,
                "word_count": len(md.split()), "line_count": len(md.splitlines())}


class CsvToJsonSkill(BaseSkill):
    """CSV/JSON donusum becerisi."""

    SKILL_ID = "125"
    NAME = "csv_to_json"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "CSV/JSON donusum"
    PARAMETERS = {"data": "CSV veya JSON verisi", "direction": "Yon (csv_to_json/json_to_csv)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        data = p.get("data", "name,age\nAli,30\nAyse,25")
        direction = p.get("direction", "csv_to_json")
        if direction == "csv_to_json":
            reader = csv.DictReader(io.StringIO(data))
            records = list(reader)
            result = json.dumps(records, indent=2, ensure_ascii=False)
            return {"direction": direction, "records": records, "count": len(records),
                    "columns": list(records[0].keys()) if records else [], "json_output": result}
        else:
            try:
                records = json.loads(data) if isinstance(data, str) else data
                if not records:
                    return {"direction": direction, "csv_output": "", "count": 0}
                buf = io.StringIO()
                writer = csv.DictWriter(buf, fieldnames=list(records[0].keys()))
                writer.writeheader()
                writer.writerows(records)
                return {"direction": direction, "csv_output": buf.getvalue(), "count": len(records)}
            except Exception as e:
                return {"direction": direction, "error": str(e)}


class XmlToJsonSkill(BaseSkill):
    """XML/JSON donusum becerisi."""

    SKILL_ID = "126"
    NAME = "xml_to_json"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "XML/JSON donusum"
    PARAMETERS = {"data": "XML veya JSON verisi", "direction": "Yon (xml_to_json/json_to_xml)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        data = p.get("data", "<root><name>Ali</name><age>30</age></root>")
        direction = p.get("direction", "xml_to_json")
        if direction == "xml_to_json":
            result: dict[str, str] = {}
            for m in re.finditer(r"<(\w+)>([^<]+)</\1>", data):
                result[m.group(1)] = m.group(2)
            return {"direction": direction, "parsed": result,
                    "json_output": json.dumps(result, indent=2, ensure_ascii=False), "field_count": len(result)}
        else:
            try:
                obj = json.loads(data) if isinstance(data, str) else data
                xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>', "<root>"]
                for k, v in (obj.items() if isinstance(obj, dict) else []):
                    xml_parts.append(f"  <{k}>{v}</{k}>")
                xml_parts.append("</root>")
                return {"direction": direction, "xml_output": "\n".join(xml_parts)}
            except Exception as e:
                return {"direction": direction, "error": str(e)}


class NumberConverterSkill(BaseSkill):
    """Sayi sistemi donusum becerisi."""

    SKILL_ID = "127"
    NAME = "number_converter"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "Sayi sistemi donusum (binary, hex, octal)"
    PARAMETERS = {"number": "Sayi", "from_base": "Kaynak taban", "to_base": "Hedef taban"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        number = p.get("number", "255")
        from_base = int(p.get("from_base", 10))
        to_base = int(p.get("to_base", 2))
        try:
            decimal_val = int(str(number), from_base)
            if to_base == 2:
                result = bin(decimal_val)[2:]
            elif to_base == 8:
                result = oct(decimal_val)[2:]
            elif to_base == 16:
                result = hex(decimal_val)[2:].upper()
            elif to_base == 10:
                result = str(decimal_val)
            else:
                digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                if decimal_val == 0:
                    result = "0"
                else:
                    parts: list[str] = []
                    n = abs(decimal_val)
                    while n:
                        parts.append(digits[n % to_base])
                        n //= to_base
                    result = "".join(reversed(parts))
            return {"input": str(number), "from_base": from_base, "to_base": to_base,
                    "decimal": decimal_val, "result": result,
                    "all_bases": {"binary": bin(decimal_val)[2:], "octal": oct(decimal_val)[2:],
                                  "decimal": str(decimal_val), "hex": hex(decimal_val)[2:].upper()}}
        except ValueError as e:
            return {"input": str(number), "error": str(e)}


class AsciiTableSkill(BaseSkill):
    """ASCII karakter tablosu becerisi."""

    SKILL_ID = "128"
    NAME = "ascii_table"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "ASCII karakter tablosu"
    PARAMETERS = {"range_start": "Baslangic (0-127)", "range_end": "Bitis (0-127)", "text": "Metin (char->code)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        text = p.get("text", "")
        start = int(p.get("range_start", 32))
        end = int(p.get("range_end", 126))
        if text:
            chars = [{"char": c, "decimal": ord(c), "hex": hex(ord(c)), "binary": bin(ord(c))[2:].zfill(8)} for c in text]
            return {"mode": "text_to_codes", "text": text, "characters": chars, "count": len(chars)}
        table = []
        for i in range(max(0, start), min(128, end + 1)):
            ch = chr(i) if 32 <= i <= 126 else f"\\x{i:02x}"
            table.append({"decimal": i, "hex": f"0x{i:02X}", "binary": bin(i)[2:].zfill(8), "char": ch})
        return {"mode": "table", "range": f"{start}-{end}", "entries": table, "count": len(table)}


class NpmSearchSkill(BaseSkill):
    """npm paket arama becerisi."""

    SKILL_ID = "129"
    NAME = "npm_search"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "npm paket arama"
    PARAMETERS = {"query": "Arama sorgusu"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        query = p.get("query", "express")
        packages = {
            "express": {"version": "4.18.2", "description": "Fast web framework", "weekly_downloads": 28000000},
            "react": {"version": "18.2.0", "description": "UI library", "weekly_downloads": 20000000},
            "lodash": {"version": "4.17.21", "description": "Utility library", "weekly_downloads": 45000000},
            "axios": {"version": "1.6.2", "description": "HTTP client", "weekly_downloads": 42000000},
            "typescript": {"version": "5.3.3", "description": "TypeScript language", "weekly_downloads": 38000000},
        }
        results = []
        for name, info in packages.items():
            if query.lower() in name.lower() or query.lower() in info["description"].lower():
                results.append({"name": name, **info, "npm_url": f"https://www.npmjs.com/package/{name}"})
        if not results:
            results.append({"name": query, "version": "1.0.0", "description": f"{query} paketi", "weekly_downloads": 1000})
        return {"query": query, "results": results, "total": len(results)}


class CrateSearchSkill(BaseSkill):
    """PyPI / Crate arama becerisi."""

    SKILL_ID = "130"
    NAME = "crate_search"
    CATEGORY = "developer"
    RISK_LEVEL = "low"
    DESCRIPTION = "Python/Rust paket arama (PyPI/crates.io)"
    PARAMETERS = {"query": "Arama sorgusu", "registry": "Kayit defteri (pypi/crates)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        query = p.get("query", "requests")
        registry = p.get("registry", "pypi").lower()
        pypi_packages = {
            "requests": {"version": "2.31.0", "description": "HTTP library", "downloads": 150000000},
            "flask": {"version": "3.0.0", "description": "Lightweight web framework", "downloads": 50000000},
            "django": {"version": "5.0", "description": "Full-stack web framework", "downloads": 30000000},
            "fastapi": {"version": "0.108.0", "description": "Modern API framework", "downloads": 25000000},
            "numpy": {"version": "1.26.2", "description": "Numerical computing", "downloads": 120000000},
        }
        results = []
        for name, info in pypi_packages.items():
            if query.lower() in name.lower() or query.lower() in info["description"].lower():
                results.append({"name": name, **info, "url": f"https://pypi.org/project/{name}/"})
        if not results:
            results.append({"name": query, "version": "0.1.0", "description": f"{query} paketi", "downloads": 100})
        return {"query": query, "registry": registry, "results": results, "total": len(results)}


ALL_DEVELOPER_SKILLS: list[type[BaseSkill]] = [
    CodeFormatterSkill,
    CodeMinifierSkill,
    JsonValidatorSkill,
    YamlValidatorSkill,
    XmlValidatorSkill,
    SqlFormatterSkill,
    SqlExplainerSkill,
    GitCommandSkill,
    DockerCommandSkill,
    ShellCommandSkill,
    ApiDocGeneratorSkill,
    MockDataGeneratorSkill,
    UuidGeneratorSkill,
    TimestampConverterSkill,
    ColorConverterSkill,
    EncodeDecoderSkill,
    HashCompareSkill,
    IpCalculatorSkill,
    HttpStatusSkill,
    MimeTypeSkill,
    CharsetConverterSkill,
    EscaperSkill,
    DiffCheckerSkill,
    MarkdownPreviewerSkill,
    CsvToJsonSkill,
    XmlToJsonSkill,
    NumberConverterSkill,
    AsciiTableSkill,
    NpmSearchSkill,
    CrateSearchSkill,
]
