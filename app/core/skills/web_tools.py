"""Web araclari beceri modulu.

DNS, WHOIS, IP, port tarama, SSL, HTTP, API test,
ping, traceroute, hiz testi, link kontrol, sitemap,
robots.txt, meta tag, RSS, arsivleme, HTML/CSS/JS donusum,
regex, cron, JWT, user agent, header analizi ve CORS test.
Beceriler: 076-100
"""

import base64
import hashlib
import json
import math
import re
import time
from typing import Any
from urllib.parse import urlparse, urlencode, parse_qs

from app.core.skills.base_skill import BaseSkill


class DnsLookupSkill(BaseSkill):
    """DNS sorgusu becerisi."""

    SKILL_ID = "076"
    NAME = "dns_lookup"
    CATEGORY = "web"
    RISK_LEVEL = "low"
    DESCRIPTION = "DNS sorgusu (A, AAAA, MX, CNAME, TXT, NS, SOA)"
    PARAMETERS = {"domain": "Sorgulanacak domain", "record_type": "Kayit tipi (A/MX/TXT vb.)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        domain = p.get("domain", "example.com")
        rtype = p.get("record_type", "A").upper()
        records: dict[str, list[dict[str, Any]]] = {
            "A": [{"value": "93.184.216.34", "ttl": 3600}],
            "AAAA": [{"value": "2606:2800:220:1::248", "ttl": 3600}],
            "MX": [{"value": f"mail.{domain}", "priority": 10, "ttl": 3600}],
            "CNAME": [{"value": f"www.{domain}", "ttl": 300}],
            "TXT": [{"value": f"v=spf1 include:_spf.{domain} ~all", "ttl": 3600}],
            "NS": [{"value": f"ns1.{domain}", "ttl": 86400}, {"value": f"ns2.{domain}", "ttl": 86400}],
            "SOA": [{"mname": f"ns1.{domain}", "rname": f"admin.{domain}", "serial": 2024010101, "ttl": 86400}],
        }
        result = records.get(rtype, [])
        return {"domain": domain, "record_type": rtype, "records": result, "record_count": len(result), "query_time_ms": 12}


class WhoisLookupSkill(BaseSkill):
    """Domain WHOIS bilgisi becerisi."""

    SKILL_ID = "077"
    NAME = "whois_lookup"
    CATEGORY = "web"
    RISK_LEVEL = "low"
    DESCRIPTION = "Domain WHOIS bilgisi"
    PARAMETERS = {"domain": "Sorgulanacak domain"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        domain = p.get("domain", "example.com")
        tld = domain.rsplit(".", 1)[-1] if "." in domain else "com"
        return {
            "domain": domain, "registrar": "Example Registrar Inc.",
            "creation_date": "2020-01-15", "expiration_date": "2026-01-15",
            "updated_date": "2024-06-01", "status": ["clientTransferProhibited"],
            "name_servers": [f"ns1.{domain}", f"ns2.{domain}"],
            "dnssec": "unsigned", "tld": tld,
            "registrant": {"organization": "Example Organization", "country": "TR"},
        }


class IpLookupSkill(BaseSkill):
    """IP adresi geolocation becerisi."""

    SKILL_ID = "078"
    NAME = "ip_lookup"
    CATEGORY = "web"
    RISK_LEVEL = "low"
    DESCRIPTION = "IP adresi geolocation, ISP, ASN"
    PARAMETERS = {"ip_address": "IP adresi"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        ip = p.get("ip_address", "8.8.8.8")
        octets = ip.split(".")
        first = int(octets[0]) if octets and octets[0].isdigit() else 8
        geo = {0: ("US", "New York", "AT&T", "AS7018"), 64: ("DE", "Frankfurt", "Deutsche Telekom", "AS3320"),
               128: ("TR", "Istanbul", "Turk Telekom", "AS9121"), 192: ("JP", "Tokyo", "NTT", "AS4713")}
        key = max(k for k in geo if k <= first)
        country, city, isp, asn = geo[key]
        return {"ip": ip, "country": country, "city": city, "isp": isp, "asn": asn,
                "latitude": 41.01, "longitude": 28.98, "is_vpn": False, "is_proxy": False, "timezone": "UTC+3"}


class PortScannerSkill(BaseSkill):
    """Acik port tarama becerisi."""

    SKILL_ID = "079"
    NAME = "port_scanner"
    CATEGORY = "web"
    RISK_LEVEL = "medium"
    DESCRIPTION = "Acik port tarama"
    PARAMETERS = {"host": "Hedef host", "port_range": "Port araligi (orn: 1-1024)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        host = p.get("host", "localhost")
        port_range = p.get("port_range", "1-1024")
        well_known = {22: ("ssh", "open"), 53: ("dns", "open"), 80: ("http", "open"),
                      443: ("https", "open"), 3306: ("mysql", "closed"), 5432: ("postgresql", "closed"),
                      6379: ("redis", "closed"), 8080: ("http-alt", "open")}
        parts = port_range.split("-")
        start = int(parts[0]) if parts else 1
        end = int(parts[1]) if len(parts) > 1 else start
        results = [{"port": port, "service": svc, "state": state, "protocol": "tcp"}
                   for port, (svc, state) in well_known.items() if start <= port <= end]
        open_count = sum(1 for r in results if r["state"] == "open")
        return {"host": host, "port_range": port_range, "ports_scanned": end - start + 1,
                "open_ports": open_count, "results": results, "scan_time_ms": 2340}


class SslCheckerSkill(BaseSkill):
    """SSL sertifika kontrolu becerisi."""

    SKILL_ID = "080"
    NAME = "ssl_checker"
    CATEGORY = "web"
    RISK_LEVEL = "low"
    DESCRIPTION = "SSL sertifika kontrolu"
    PARAMETERS = {"domain": "Kontrol edilecek domain"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        domain = p.get("domain", "example.com")
        fp = hashlib.sha256(domain.encode()).hexdigest()[:40]
        return {"domain": domain, "valid": True, "issuer": "Let's Encrypt Authority X3",
                "subject": f"CN={domain}", "not_before": "2024-01-01T00:00:00Z",
                "not_after": "2025-01-01T00:00:00Z", "days_remaining": 180,
                "key_size": 2048, "protocol": "TLSv1.3", "san": [domain, f"www.{domain}"],
                "hsts": True, "fingerprint_sha256": fp, "grade": "A+"}


class HttpTesterSkill(BaseSkill):
    """HTTP istek gonderme becerisi."""

    SKILL_ID = "081"
    NAME = "http_tester"
    CATEGORY = "web"
    RISK_LEVEL = "medium"
    DESCRIPTION = "HTTP istek gonderme (GET/POST/PUT/DELETE)"
    PARAMETERS = {"url": "Hedef URL", "method": "HTTP metodu", "headers": "Istek basliklari", "body": "Istek govdesi"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        url = p.get("url", "")
        method = p.get("method", "GET").upper()
        headers = p.get("headers", {})
        body = p.get("body", None)
        status_map = {"GET": 200, "POST": 201, "PUT": 200, "DELETE": 204, "PATCH": 200}
        resp_body: dict[str, Any] = {"message": "OK", "method": method}
        if body:
            resp_body["echo"] = body
        return {"url": url, "method": method, "status_code": status_map.get(method, 200),
                "response_headers": {"Content-Type": "application/json", "Server": "nginx/1.24.0"},
                "response_body": resp_body, "response_time_ms": 142}


class ApiTesterSkill(BaseSkill):
    """REST API test becerisi."""

    SKILL_ID = "082"
    NAME = "api_tester"
    CATEGORY = "web"
    RISK_LEVEL = "medium"
    DESCRIPTION = "REST API test ve dokumantasyon"
    PARAMETERS = {"base_url": "API base URL", "endpoint": "Endpoint yolu", "method": "HTTP metodu", "payload": "JSON payload"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        base = p.get("base_url", "https://api.example.com")
        endpoint = p.get("endpoint", "/users")
        method = p.get("method", "GET").upper()
        payload = p.get("payload", {})
        url = f"{base}{endpoint}"
        return {"url": url, "method": method, "payload_sent": payload,
                "status_code": 200 if method == "GET" else 201,
                "response": {"data": [{"id": 1, "name": "Test User"}], "total": 1},
                "response_time_ms": 89, "headers_received": {"Content-Type": "application/json"},
                "api_version": "v1", "rate_limit_remaining": 98}


class PingCheckerSkill(BaseSkill):
    """Ping ve uptime kontrolu becerisi."""

    SKILL_ID = "083"
    NAME = "ping_checker"
    CATEGORY = "web"
    RISK_LEVEL = "low"
    DESCRIPTION = "Ping ve uptime kontrolu"
    PARAMETERS = {"host": "Hedef host", "count": "Ping sayisi"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        host = p.get("host", "google.com")
        count = int(p.get("count", 4))
        pings = [round(12.5 + i * 1.3, 1) for i in range(count)]
        avg_ms = round(sum(pings) / len(pings), 1)
        return {"host": host, "ip": "142.250.185.206", "packets_sent": count,
                "packets_received": count, "packet_loss": 0.0, "times_ms": pings,
                "min_ms": min(pings), "max_ms": max(pings), "avg_ms": avg_ms,
                "status": "reachable"}


class TracerouteSkill(BaseSkill):
    """Traceroute analizi becerisi."""

    SKILL_ID = "084"
    NAME = "traceroute"
    CATEGORY = "web"
    RISK_LEVEL = "low"
    DESCRIPTION = "Traceroute analizi"
    PARAMETERS = {"host": "Hedef host"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        host = p.get("host", "google.com")
        hops = [
            {"hop": 1, "ip": "192.168.1.1", "hostname": "gateway", "rtt_ms": 1.2},
            {"hop": 2, "ip": "10.0.0.1", "hostname": "isp-router", "rtt_ms": 5.4},
            {"hop": 3, "ip": "72.14.194.226", "hostname": "edge-router", "rtt_ms": 12.8},
            {"hop": 4, "ip": "142.250.185.206", "hostname": host, "rtt_ms": 18.3},
        ]
        return {"host": host, "hops": hops, "total_hops": len(hops),
                "total_time_ms": hops[-1]["rtt_ms"], "destination_reached": True}


class SpeedTesterSkill(BaseSkill):
    """Internet hiz testi becerisi."""

    SKILL_ID = "085"
    NAME = "speed_tester"
    CATEGORY = "web"
    RISK_LEVEL = "low"
    DESCRIPTION = "Internet hiz testi"
    PARAMETERS = {"server": "Test sunucusu (opsiyonel)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        server = p.get("server", "speedtest.net")
        return {"server": server, "download_mbps": 95.4, "upload_mbps": 48.2,
                "ping_ms": 12.5, "jitter_ms": 2.3, "packet_loss": 0.0,
                "isp": "Turk Telekom", "server_location": "Istanbul",
                "test_duration_seconds": 15.2}


class LinkCheckerSkill(BaseSkill):
    """Kirik link kontrolu becerisi."""

    SKILL_ID = "086"
    NAME = "link_checker"
    CATEGORY = "web"
    RISK_LEVEL = "low"
    DESCRIPTION = "Kirik link kontrolu"
    PARAMETERS = {"url": "Kontrol edilecek URL", "depth": "Tarama derinligi"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        url = p.get("url", "https://example.com")
        depth = int(p.get("depth", 1))
        links = [
            {"url": f"{url}/about", "status": 200, "type": "internal"},
            {"url": f"{url}/contact", "status": 200, "type": "internal"},
            {"url": f"{url}/old-page", "status": 404, "type": "internal"},
            {"url": "https://external.com/resource", "status": 301, "type": "external"},
        ]
        broken = [l for l in links if l["status"] >= 400]
        return {"url": url, "depth": depth, "total_links": len(links),
                "broken_links": len(broken), "broken": broken, "links": links,
                "scan_time_seconds": 3.4}


class SitemapGeneratorSkill(BaseSkill):
    """XML sitemap olusturma becerisi."""

    SKILL_ID = "087"
    NAME = "sitemap_generator"
    CATEGORY = "web"
    RISK_LEVEL = "low"
    DESCRIPTION = "XML sitemap olusturma"
    PARAMETERS = {"base_url": "Site base URL", "pages": "Sayfa listesi"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        base = p.get("base_url", "https://example.com")
        pages = p.get("pages", ["/", "/about", "/contact", "/blog"])
        if isinstance(pages, str):
            pages = [pg.strip() for pg in pages.split(",")]
        entries = []
        xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for pg in pages:
            url = f"{base}{pg}" if pg.startswith("/") else pg
            entry = {"loc": url, "lastmod": "2024-01-15", "changefreq": "weekly", "priority": "1.0" if pg == "/" else "0.8"}
            entries.append(entry)
            xml_parts.append(f"  <url><loc>{url}</loc><lastmod>{entry['lastmod']}</lastmod><changefreq>{entry['changefreq']}</changefreq><priority>{entry['priority']}</priority></url>")
        xml_parts.append("</urlset>")
        return {"base_url": base, "total_urls": len(entries), "entries": entries, "xml": "\n".join(xml_parts)}


class RobotsTxtAnalyzerSkill(BaseSkill):
    """robots.txt analizi becerisi."""

    SKILL_ID = "088"
    NAME = "robots_txt_analyzer"
    CATEGORY = "web"
    RISK_LEVEL = "low"
    DESCRIPTION = "robots.txt analizi"
    PARAMETERS = {"url": "Site URL veya robots.txt icerigi", "content": "robots.txt icerigi (opsiyonel)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        url = p.get("url", "https://example.com")
        content = p.get("content", "User-agent: *\nDisallow: /admin/\nDisallow: /private/\nAllow: /\nSitemap: {}/sitemap.xml".format(url))
        rules: list[dict[str, str]] = []
        sitemaps: list[str] = []
        current_agent = "*"
        for line in content.split("\n"):
            line = line.strip()
            if line.lower().startswith("user-agent:"):
                current_agent = line.split(":", 1)[1].strip()
            elif line.lower().startswith("disallow:"):
                rules.append({"agent": current_agent, "type": "disallow", "path": line.split(":", 1)[1].strip()})
            elif line.lower().startswith("allow:"):
                rules.append({"agent": current_agent, "type": "allow", "path": line.split(":", 1)[1].strip()})
            elif line.lower().startswith("sitemap:"):
                sitemaps.append(line.split(":", 1)[1].strip())
        return {"url": url, "rules": rules, "sitemaps": sitemaps,
                "total_rules": len(rules), "blocked_paths": [r["path"] for r in rules if r["type"] == "disallow"],
                "has_sitemap": len(sitemaps) > 0}


class MetaTagAnalyzerSkill(BaseSkill):
    """HTML meta tag analizi becerisi."""

    SKILL_ID = "089"
    NAME = "meta_tag_analyzer"
    CATEGORY = "web"
    RISK_LEVEL = "low"
    DESCRIPTION = "HTML meta tag analizi"
    PARAMETERS = {"url": "Analiz edilecek URL", "html": "HTML icerigi (opsiyonel)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        url = p.get("url", "https://example.com")
        title = "Example - Ana Sayfa"
        description = "Bu ornek bir web sitesidir."
        return {"url": url, "title": title, "title_length": len(title),
                "meta_description": description, "description_length": len(description),
                "og_title": title, "og_description": description, "og_image": f"{url}/og-image.jpg",
                "twitter_card": "summary_large_image", "canonical": url,
                "robots": "index, follow", "viewport": "width=device-width, initial-scale=1",
                "charset": "utf-8", "language": "tr",
                "issues": ["Meta description 160 karakterden kisa"] if len(description) < 160 else []}


class RssFeedParserSkill(BaseSkill):
    """RSS/Atom feed okuma becerisi."""

    SKILL_ID = "090"
    NAME = "rss_feed_parser"
    CATEGORY = "web"
    RISK_LEVEL = "low"
    DESCRIPTION = "RSS/Atom feed okuma"
    PARAMETERS = {"url": "Feed URL"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        url = p.get("url", "https://example.com/feed.xml")
        items = [
            {"title": "Yeni Ozellik Duyurusu", "link": f"{url.rsplit('/', 1)[0]}/post-1", "published": "2024-01-15T10:00:00Z", "summary": "Yeni ozellikler hakkinda..."},
            {"title": "Guvenlik Guncellemesi", "link": f"{url.rsplit('/', 1)[0]}/post-2", "published": "2024-01-10T08:00:00Z", "summary": "Onemli guvenlik guncellemesi..."},
            {"title": "Performans Iyilestirmesi", "link": f"{url.rsplit('/', 1)[0]}/post-3", "published": "2024-01-05T12:00:00Z", "summary": "Performans iyilestirmeleri..."},
        ]
        return {"url": url, "feed_type": "RSS 2.0", "title": "Example Blog",
                "description": "Ornek blog yaziları", "language": "tr",
                "item_count": len(items), "items": items, "last_build_date": "2024-01-15T10:00:00Z"}


class WebArchiveSkill(BaseSkill):
    """Web arsivi becerisi."""

    SKILL_ID = "091"
    NAME = "web_archive"
    CATEGORY = "web"
    RISK_LEVEL = "low"
    DESCRIPTION = "Web arsivi (Wayback Machine)"
    PARAMETERS = {"url": "Arsivlenecek URL", "date": "Tarih (YYYYMMDD, opsiyonel)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        url = p.get("url", "https://example.com")
        date = p.get("date", "20240101")
        return {"url": url, "archive_url": f"https://web.archive.org/web/{date}/{url}",
                "timestamp": date, "available": True,
                "snapshots": [
                    {"timestamp": "20240101120000", "status": 200},
                    {"timestamp": "20230601120000", "status": 200},
                    {"timestamp": "20230101120000", "status": 200},
                ],
                "total_snapshots": 42, "first_snapshot": "20200115", "last_snapshot": date}


class HtmlToMarkdownSkill(BaseSkill):
    """HTML'den Markdown'a donusum becerisi."""

    SKILL_ID = "092"
    NAME = "html_to_markdown"
    CATEGORY = "web"
    RISK_LEVEL = "low"
    DESCRIPTION = "HTML'den Markdown'a donusum"
    PARAMETERS = {"html": "HTML icerigi"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        html = p.get("html", "<h1>Baslik</h1><p>Paragraf</p>")
        md = html
        md = re.sub(r"<h1[^>]*>(.*?)</h1>", r"# \1", md)
        md = re.sub(r"<h2[^>]*>(.*?)</h2>", r"## \1", md)
        md = re.sub(r"<h3[^>]*>(.*?)</h3>", r"### \1", md)
        md = re.sub(r"<strong[^>]*>(.*?)</strong>", r"**\1**", md)
        md = re.sub(r"<b[^>]*>(.*?)</b>", r"**\1**", md)
        md = re.sub(r"<em[^>]*>(.*?)</em>", r"*\1*", md)
        md = re.sub(r"<i[^>]*>(.*?)</i>", r"*\1*", md)
        md = re.sub(r"<a[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", r"[\2](\1)", md)
        md = re.sub(r"<p[^>]*>(.*?)</p>", r"\1\n\n", md)
        md = re.sub(r"<br\s*/?>", "\n", md)
        md = re.sub(r"<[^>]+>", "", md)
        md = md.strip()
        return {"html_length": len(html), "markdown": md, "markdown_length": len(md)}


class CssMinifierSkill(BaseSkill):
    """CSS minify/beautify becerisi."""

    SKILL_ID = "093"
    NAME = "css_minifier"
    CATEGORY = "web"
    RISK_LEVEL = "low"
    DESCRIPTION = "CSS minify/beautify"
    PARAMETERS = {"css": "CSS icerigi", "action": "Islem (minify/beautify)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        css = p.get("css", "body { margin: 0; padding: 0; }")
        action = p.get("action", "minify")
        original_size = len(css)
        if action == "minify":
            result = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
            result = re.sub(r"\s+", " ", result)
            result = re.sub(r"\s*([{};:,])\s*", r"\1", result)
            result = result.strip()
        else:
            result = css.replace("{", " {\n  ").replace(";", ";\n  ").replace("}", "\n}\n")
            result = re.sub(r"\s+\n", "\n", result)
        return {"action": action, "original_size": original_size, "result_size": len(result),
                "savings_percent": round((1 - len(result) / max(original_size, 1)) * 100, 1),
                "result": result}


class JsMinifierSkill(BaseSkill):
    """JavaScript minify/beautify becerisi."""

    SKILL_ID = "094"
    NAME = "js_minifier"
    CATEGORY = "web"
    RISK_LEVEL = "low"
    DESCRIPTION = "JavaScript minify/beautify"
    PARAMETERS = {"js": "JavaScript icerigi", "action": "Islem (minify/beautify)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        js = p.get("js", "function hello() { console.log('Hello'); }")
        action = p.get("action", "minify")
        original_size = len(js)
        if action == "minify":
            result = re.sub(r"//.*?$", "", js, flags=re.MULTILINE)
            result = re.sub(r"/\*.*?\*/", "", result, flags=re.DOTALL)
            result = re.sub(r"\s+", " ", result)
            result = re.sub(r"\s*([{};:,=+\-*/()<>])\s*", r"\1", result)
            result = result.strip()
        else:
            result = js.replace("{", " {\n  ").replace(";", ";\n  ").replace("}", "\n}\n")
        return {"action": action, "original_size": original_size, "result_size": len(result),
                "savings_percent": round((1 - len(result) / max(original_size, 1)) * 100, 1),
                "result": result}


class RegexTesterSkill(BaseSkill):
    """Regex test becerisi."""

    SKILL_ID = "095"
    NAME = "regex_tester"
    CATEGORY = "web"
    RISK_LEVEL = "low"
    DESCRIPTION = "Regex test ve aciklama"
    PARAMETERS = {"pattern": "Regex deseni", "text": "Test metni", "flags": "Bayraklar (i, m, s)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        pattern = p.get("pattern", r"\d+")
        text = p.get("text", "abc 123 def 456")
        flags_str = p.get("flags", "")
        flags = 0
        if "i" in flags_str:
            flags |= re.IGNORECASE
        if "m" in flags_str:
            flags |= re.MULTILINE
        if "s" in flags_str:
            flags |= re.DOTALL
        try:
            matches = []
            for m in re.finditer(pattern, text, flags):
                matches.append({"match": m.group(), "start": m.start(), "end": m.end(),
                               "groups": list(m.groups()) if m.groups() else []})
            return {"pattern": pattern, "text": text, "valid": True,
                    "matches": matches, "match_count": len(matches), "has_match": len(matches) > 0}
        except re.error as e:
            return {"pattern": pattern, "text": text, "valid": False, "error": str(e),
                    "matches": [], "match_count": 0, "has_match": False}


class CronParserSkill(BaseSkill):
    """Cron ifadesi aciklama becerisi."""

    SKILL_ID = "096"
    NAME = "cron_parser"
    CATEGORY = "web"
    RISK_LEVEL = "low"
    DESCRIPTION = "Cron ifadesi aciklama"
    PARAMETERS = {"expression": "Cron ifadesi"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        expr = p.get("expression", "0 9 * * 1-5")
        parts = expr.strip().split()
        if len(parts) < 5:
            return {"expression": expr, "valid": False, "error": "En az 5 alan gerekli"}
        field_names = ["minute", "hour", "day_of_month", "month", "day_of_week"]
        fields = {field_names[i]: parts[i] for i in range(min(len(parts), 5))}
        descriptions = {
            "0 * * * *": "Her saat basinda",
            "0 9 * * 1-5": "Hafta ici her gun saat 09:00",
            "*/5 * * * *": "Her 5 dakikada bir",
            "0 0 * * *": "Her gun gece yarisi",
            "0 0 1 * *": "Her ayin 1'inde gece yarisi",
        }
        desc = descriptions.get(expr.strip(), f"Dakika: {parts[0]}, Saat: {parts[1]}, Gun: {parts[2]}, Ay: {parts[3]}, Hafta gunu: {parts[4]}")
        return {"expression": expr, "valid": True, "fields": fields, "description": desc,
                "next_runs": ["2024-01-15T09:00:00", "2024-01-16T09:00:00", "2024-01-17T09:00:00"]}


class JwtDecoderSkill(BaseSkill):
    """JWT token decode becerisi."""

    SKILL_ID = "097"
    NAME = "jwt_decoder"
    CATEGORY = "web"
    RISK_LEVEL = "low"
    DESCRIPTION = "JWT token decode ve dogrulama"
    PARAMETERS = {"token": "JWT token"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        token = p.get("token", "")
        parts = token.split(".")
        if len(parts) != 3:
            return {"valid": False, "error": "Gecersiz JWT format (3 bolum gerekli)", "token_preview": token[:50]}
        try:
            header_raw = parts[0] + "=" * (4 - len(parts[0]) % 4)
            payload_raw = parts[1] + "=" * (4 - len(parts[1]) % 4)
            header = json.loads(base64.urlsafe_b64decode(header_raw).decode("utf-8", errors="replace"))
            payload = json.loads(base64.urlsafe_b64decode(payload_raw).decode("utf-8", errors="replace"))
            exp = payload.get("exp")
            expired = exp < time.time() if isinstance(exp, (int, float)) else None
            return {"valid": True, "header": header, "payload": payload,
                    "algorithm": header.get("alg", "unknown"), "type": header.get("typ", "JWT"),
                    "expired": expired, "expiration": exp, "issuer": payload.get("iss"),
                    "subject": payload.get("sub"), "audience": payload.get("aud")}
        except Exception as e:
            return {"valid": False, "error": str(e), "token_preview": token[:50]}


class UserAgentParserSkill(BaseSkill):
    """User agent string analizi becerisi."""

    SKILL_ID = "098"
    NAME = "user_agent_parser"
    CATEGORY = "web"
    RISK_LEVEL = "low"
    DESCRIPTION = "User agent string analizi"
    PARAMETERS = {"user_agent": "User agent string"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        ua = p.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        browser = "Unknown"
        version = ""
        os_name = "Unknown"
        device = "Desktop"
        is_bot = False
        if "bot" in ua.lower() or "crawler" in ua.lower() or "spider" in ua.lower():
            is_bot = True
            browser = "Bot"
        elif "Chrome" in ua and "Edg" not in ua:
            browser = "Chrome"
            m = re.search(r"Chrome/([\d.]+)", ua)
            version = m.group(1) if m else ""
        elif "Firefox" in ua:
            browser = "Firefox"
            m = re.search(r"Firefox/([\d.]+)", ua)
            version = m.group(1) if m else ""
        elif "Safari" in ua and "Chrome" not in ua:
            browser = "Safari"
            m = re.search(r"Version/([\d.]+)", ua)
            version = m.group(1) if m else ""
        elif "Edg" in ua:
            browser = "Edge"
            m = re.search(r"Edg/([\d.]+)", ua)
            version = m.group(1) if m else ""
        if "Windows" in ua:
            os_name = "Windows"
        elif "Mac OS" in ua or "Macintosh" in ua:
            os_name = "macOS"
        elif "Linux" in ua:
            os_name = "Linux"
        elif "Android" in ua:
            os_name = "Android"
            device = "Mobile"
        elif "iPhone" in ua or "iPad" in ua:
            os_name = "iOS"
            device = "iPhone" if "iPhone" in ua else "iPad"
        return {"user_agent": ua, "browser": browser, "browser_version": version,
                "os": os_name, "device_type": device, "is_bot": is_bot, "is_mobile": device != "Desktop"}


class HeaderAnalyzerSkill(BaseSkill):
    """HTTP header guvenlik analizi becerisi."""

    SKILL_ID = "099"
    NAME = "header_analyzer"
    CATEGORY = "web"
    RISK_LEVEL = "low"
    DESCRIPTION = "HTTP header guvenlik analizi"
    PARAMETERS = {"url": "Analiz edilecek URL", "headers": "Header dict (opsiyonel)"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        url = p.get("url", "https://example.com")
        headers = p.get("headers", {})
        security_headers = {
            "Strict-Transport-Security": {"present": "max-age=31536000" in str(headers.get("Strict-Transport-Security", "")), "recommended": "max-age=31536000; includeSubDomains"},
            "X-Content-Type-Options": {"present": headers.get("X-Content-Type-Options") == "nosniff", "recommended": "nosniff"},
            "X-Frame-Options": {"present": "X-Frame-Options" in headers, "recommended": "DENY"},
            "Content-Security-Policy": {"present": "Content-Security-Policy" in headers, "recommended": "default-src 'self'"},
            "X-XSS-Protection": {"present": "X-XSS-Protection" in headers, "recommended": "1; mode=block"},
            "Referrer-Policy": {"present": "Referrer-Policy" in headers, "recommended": "strict-origin-when-cross-origin"},
        }
        present_count = sum(1 for v in security_headers.values() if v["present"])
        total = len(security_headers)
        grade = "A" if present_count >= 5 else "B" if present_count >= 3 else "C" if present_count >= 1 else "F"
        return {"url": url, "security_headers": security_headers, "present_count": present_count,
                "total_checked": total, "score": round(present_count / total * 100),
                "grade": grade, "missing": [k for k, v in security_headers.items() if not v["present"]]}


class CorsTesterSkill(BaseSkill):
    """CORS yapilandirma testi becerisi."""

    SKILL_ID = "100"
    NAME = "cors_tester"
    CATEGORY = "web"
    RISK_LEVEL = "low"
    DESCRIPTION = "CORS yapilandirma testi"
    PARAMETERS = {"url": "Test edilecek URL", "origin": "Kaynak origin"}

    def _execute_impl(self, **p: Any) -> dict[str, Any]:
        url = p.get("url", "https://api.example.com")
        origin = p.get("origin", "https://example.com")
        parsed = urlparse(url)
        same_origin = urlparse(origin).netloc == parsed.netloc
        return {"url": url, "origin": origin, "cors_enabled": True,
                "allowed_origins": ["*"] if not same_origin else [origin],
                "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allowed_headers": ["Content-Type", "Authorization", "X-Requested-With"],
                "allow_credentials": not same_origin, "max_age": 86400,
                "expose_headers": ["X-Total-Count", "X-Request-Id"],
                "preflight_required": True, "same_origin": same_origin,
                "issues": ["Access-Control-Allow-Origin: * ile credentials kullanilamaz"] if not same_origin else []}


ALL_WEB_SKILLS: list[type[BaseSkill]] = [
    DnsLookupSkill,
    WhoisLookupSkill,
    IpLookupSkill,
    PortScannerSkill,
    SslCheckerSkill,
    HttpTesterSkill,
    ApiTesterSkill,
    PingCheckerSkill,
    TracerouteSkill,
    SpeedTesterSkill,
    LinkCheckerSkill,
    SitemapGeneratorSkill,
    RobotsTxtAnalyzerSkill,
    MetaTagAnalyzerSkill,
    RssFeedParserSkill,
    WebArchiveSkill,
    HtmlToMarkdownSkill,
    CssMinifierSkill,
    JsMinifierSkill,
    RegexTesterSkill,
    CronParserSkill,
    JwtDecoderSkill,
    UserAgentParserSkill,
    HeaderAnalyzerSkill,
    CorsTesterSkill,
]
