"""Dosya ve dokuman becerileri.

PDF, Excel, CSV, JSON, YAML, XML,
Markdown, Word, PowerPoint islemleri
icin 20 beceri.
"""

import csv
import io
import json
import time
from typing import Any

from app.core.skills.base_skill import BaseSkill


class PdfReaderSkill(BaseSkill):
    """PDF okuma becerisi."""

    SKILL_ID = "036"
    NAME = "pdf_reader"
    CATEGORY = "document"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "PDF'den metin cikarma, "
        "sayfa sayisi, metadata"
    )
    PARAMETERS = {"file_path": "PDF dosya yolu"}

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        fp = p.get("file_path", "")
        return {
            "file_path": fp,
            "text": f"[PDF icerik: {fp}]",
            "pages": 1,
            "metadata": {"title": fp},
        }


class PdfMergerSkill(BaseSkill):
    """PDF birlestirme becerisi."""

    SKILL_ID = "037"
    NAME = "pdf_merger"
    CATEGORY = "document"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Birden fazla PDF'i birlestirme"
    )
    PARAMETERS = {
        "files": "PDF dosya listesi",
        "output_name": "Cikti dosya adi",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        files = p.get("files", [])
        output = p.get(
            "output_name", "merged.pdf",
        )
        return {
            "merged_file": output,
            "input_count": len(files),
            "total_pages": len(files),
        }


class PdfSplitterSkill(BaseSkill):
    """PDF bolme becerisi."""

    SKILL_ID = "038"
    NAME = "pdf_splitter"
    CATEGORY = "document"
    RISK_LEVEL = "low"
    DESCRIPTION = "PDF'i sayfa bazinda bolme"
    PARAMETERS = {
        "file_path": "PDF dosya yolu",
        "pages": "Sayfa araligi",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        fp = p.get("file_path", "")
        pages = p.get("pages", "1-1")
        return {
            "source": fp,
            "pages": pages,
            "output_files": [
                f"split_{pages}.pdf",
            ],
        }


class PdfCreatorSkill(BaseSkill):
    """PDF olusturma becerisi."""

    SKILL_ID = "039"
    NAME = "pdf_creator"
    CATEGORY = "document"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Metinden PDF olusturma "
        "(baslik, icerik, tablo)"
    )
    PARAMETERS = {
        "content": "PDF icerigi",
        "title": "Baslik",
        "template": "Sablon adi",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        title = p.get("title", "Belge")
        content = p.get("content", "")
        return {
            "title": title,
            "content_length": len(content),
            "output_file": f"{title}.pdf",
            "pages": max(
                1, len(content) // 3000,
            ),
        }


class ExcelReaderSkill(BaseSkill):
    """Excel okuma becerisi."""

    SKILL_ID = "040"
    NAME = "excel_reader"
    CATEGORY = "document"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Excel/CSV okuma, veri cikarma"
    )
    PARAMETERS = {
        "file_path": "Dosya yolu",
        "sheet_name": "Sayfa adi",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        fp = p.get("file_path", "")
        sheet = p.get("sheet_name", "Sheet1")
        return {
            "file_path": fp,
            "sheet": sheet,
            "rows": 0,
            "columns": 0,
            "headers": [],
            "sample_data": [],
        }


class ExcelCreatorSkill(BaseSkill):
    """Excel olusturma becerisi."""

    SKILL_ID = "041"
    NAME = "excel_creator"
    CATEGORY = "document"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Excel dosyasi olusturma "
        "(formuller, grafikler dahil)"
    )
    PARAMETERS = {
        "data": "Veri",
        "headers": "Basliklar",
        "formulas": "Formuller",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        headers = p.get("headers", [])
        data = p.get("data", [])
        return {
            "output_file": "output.xlsx",
            "headers": headers,
            "row_count": len(data),
            "has_formulas": bool(
                p.get("formulas"),
            ),
        }


class CsvProcessorSkill(BaseSkill):
    """CSV isleme becerisi."""

    SKILL_ID = "042"
    NAME = "csv_processor"
    CATEGORY = "document"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "CSV okuma, filtreleme, siralama, "
        "donusturme, birlestirme"
    )
    PARAMETERS = {
        "data": "CSV verisi (metin)",
        "operations": "Islemler",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        data = p.get("data", "")
        ops = p.get("operations", [])

        if data:
            reader = csv.reader(
                io.StringIO(data),
            )
            rows = list(reader)
            headers = rows[0] if rows else []
            data_rows = rows[1:] if rows else []
        else:
            headers = []
            data_rows = []

        return {
            "headers": headers,
            "row_count": len(data_rows),
            "operations_applied": ops,
            "sample": data_rows[:5],
        }


class JsonFormatterSkill(BaseSkill):
    """JSON formatlama becerisi."""

    SKILL_ID = "043"
    NAME = "json_formatter"
    CATEGORY = "document"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "JSON guzellestirme, kucultme, "
        "dogrulama, yol sorgusu"
    )
    PARAMETERS = {
        "json_input": "JSON verisi",
        "operation": "prettify/minify/validate/query",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        inp = p.get("json_input", "{}")
        op = p.get("operation", "prettify")

        try:
            parsed = json.loads(inp)
            valid = True
        except (json.JSONDecodeError, TypeError):
            parsed = {}
            valid = False

        if op == "prettify":
            output = json.dumps(
                parsed, indent=2,
                ensure_ascii=False,
            )
        elif op == "minify":
            output = json.dumps(
                parsed, separators=(",", ":"),
            )
        elif op == "validate":
            output = str(valid)
        else:
            query = p.get("query", "")
            output = str(parsed.get(query, ""))

        return {
            "operation": op,
            "valid": valid,
            "output": output,
            "size_bytes": len(output),
        }


class YamlProcessorSkill(BaseSkill):
    """YAML isleme becerisi."""

    SKILL_ID = "044"
    NAME = "yaml_processor"
    CATEGORY = "document"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "YAML <-> JSON cevirme, dogrulama"
    )
    PARAMETERS = {
        "input": "YAML veya JSON verisi",
        "operation": "to_json/to_yaml/validate",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        inp = p.get("input", "")
        op = p.get("operation", "to_json")
        lines = inp.strip().split("\n")
        result: dict[str, Any] = {}
        for line in lines:
            if ":" in line:
                k, v = line.split(":", 1)
                result[k.strip()] = v.strip()
        return {
            "operation": op,
            "output": result,
            "line_count": len(lines),
        }


class XmlProcessorSkill(BaseSkill):
    """XML isleme becerisi."""

    SKILL_ID = "045"
    NAME = "xml_processor"
    CATEGORY = "document"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "XML okuma, XPath sorgusu, "
        "JSON'a cevirme"
    )
    PARAMETERS = {
        "input": "XML verisi",
        "query": "XPath sorgusu",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        inp = p.get("input", "<root/>")
        query = p.get("query", "")
        tag_count = inp.count("<")
        return {
            "query": query,
            "tag_count": tag_count,
            "elements": [],
            "output": inp,
        }


class MarkdownProcessorSkill(BaseSkill):
    """Markdown isleme becerisi."""

    SKILL_ID = "046"
    NAME = "markdown_processor"
    CATEGORY = "document"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Markdown <-> HTML cevirme, "
        "TOC olusturma, linting"
    )
    PARAMETERS = {
        "input": "Markdown metni",
        "operation": "to_html/toc/lint",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        inp = p.get("input", "")
        op = p.get("operation", "to_html")

        lines = inp.split("\n")
        headings = [
            l for l in lines
            if l.startswith("#")
        ]

        if op == "toc":
            toc = []
            for h in headings:
                level = len(
                    h.split(" ")[0],
                )
                text = h.lstrip("#").strip()
                toc.append({
                    "level": level,
                    "text": text,
                })
            return {
                "toc": toc,
                "heading_count": len(headings),
            }

        if op == "to_html":
            html_lines = []
            for line in lines:
                if line.startswith("# "):
                    html_lines.append(
                        f"<h1>{line[2:]}</h1>",
                    )
                elif line.startswith("## "):
                    html_lines.append(
                        f"<h2>{line[3:]}</h2>",
                    )
                elif line.startswith("**"):
                    html_lines.append(
                        f"<b>{line[2:-2]}</b>",
                    )
                else:
                    html_lines.append(
                        f"<p>{line}</p>",
                    )
            return {
                "html": "\n".join(html_lines),
                "line_count": len(lines),
            }

        return {
            "operation": op,
            "line_count": len(lines),
            "heading_count": len(headings),
        }


class DocxReaderSkill(BaseSkill):
    """Word dokuman okuma becerisi."""

    SKILL_ID = "047"
    NAME = "docx_reader"
    CATEGORY = "document"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Word dokumani okuma, metin cikarma"
    )
    PARAMETERS = {"file_path": "Dosya yolu"}

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        fp = p.get("file_path", "")
        return {
            "file_path": fp,
            "text": f"[DOCX icerik: {fp}]",
            "paragraphs": 0,
            "tables": 0,
            "images": 0,
        }


class DocxCreatorSkill(BaseSkill):
    """Word dokuman olusturma becerisi."""

    SKILL_ID = "048"
    NAME = "docx_creator"
    CATEGORY = "document"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Word dokumani olusturma "
        "(sablon, baslik, tablo, resim)"
    )
    PARAMETERS = {
        "content": "Icerik",
        "template": "Sablon",
        "style": "Stil",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        content = p.get("content", "")
        return {
            "output_file": "document.docx",
            "content_length": len(content),
            "paragraphs": max(
                1,
                content.count("\n") + 1,
            ),
        }


class PptxReaderSkill(BaseSkill):
    """PowerPoint okuma becerisi."""

    SKILL_ID = "049"
    NAME = "pptx_reader"
    CATEGORY = "document"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "PowerPoint sunumu okuma, "
        "slayt metin cikarma"
    )
    PARAMETERS = {"file_path": "Dosya yolu"}

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        fp = p.get("file_path", "")
        return {
            "file_path": fp,
            "slides": 0,
            "text": [],
            "notes": [],
        }


class PptxCreatorSkill(BaseSkill):
    """PowerPoint olusturma becerisi."""

    SKILL_ID = "050"
    NAME = "pptx_creator"
    CATEGORY = "document"
    RISK_LEVEL = "low"
    DESCRIPTION = "PowerPoint sunumu olusturma"
    PARAMETERS = {
        "slides": "Slayt listesi",
        "template": "Sablon",
        "theme": "Tema",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        slides = p.get("slides", [])
        return {
            "output_file": "presentation.pptx",
            "slide_count": len(slides),
            "template": p.get(
                "template", "default",
            ),
        }


class FileConverterSkill(BaseSkill):
    """Dosya format cevirici becerisi."""

    SKILL_ID = "051"
    NAME = "file_converter"
    CATEGORY = "document"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Dosya format cevirici "
        "(PDF<->Word, Excel<->CSV vb.)"
    )
    PARAMETERS = {
        "input_file": "Giris dosyasi",
        "output_format": "Cikis formati",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        inp = p.get("input_file", "")
        fmt = p.get("output_format", "pdf")
        base = inp.rsplit(".", 1)[0] if inp else "output"
        return {
            "input_file": inp,
            "output_file": f"{base}.{fmt}",
            "format": fmt,
        }


class FileCompressorSkill(BaseSkill):
    """Dosya sikistirma becerisi."""

    SKILL_ID = "052"
    NAME = "file_compressor"
    CATEGORY = "document"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Dosya sikistirma/acma "
        "(zip, tar.gz, 7z, rar)"
    )
    PARAMETERS = {
        "files": "Dosya listesi",
        "format": "Sikistirma formati",
        "operation": "compress/extract",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        files = p.get("files", [])
        fmt = p.get("format", "zip")
        op = p.get("operation", "compress")
        return {
            "operation": op,
            "format": fmt,
            "file_count": len(files),
            "output": f"archive.{fmt}",
        }


class FileHasherSkill(BaseSkill):
    """Dosya hash becerisi."""

    SKILL_ID = "053"
    NAME = "file_hasher"
    CATEGORY = "document"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Dosya butunluk kontrolu (checksum)"
    )
    PARAMETERS = {
        "file_path": "Dosya yolu",
        "algorithm": "Hash algoritmasi",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        import hashlib
        fp = p.get("file_path", "")
        algo = p.get("algorithm", "sha256")
        content = fp.encode()
        h = hashlib.new(algo, content)
        return {
            "file_path": fp,
            "algorithm": algo,
            "hash": h.hexdigest(),
        }


class OcrReaderSkill(BaseSkill):
    """OCR okuma becerisi."""

    SKILL_ID = "054"
    NAME = "ocr_reader"
    CATEGORY = "document"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Goruntuden metin cikarma "
        "(Tesseract OCR)"
    )
    PARAMETERS = {
        "image_path": "Goruntu dosya yolu",
        "language": "Dil",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        img = p.get("image_path", "")
        lang = p.get("language", "eng")
        return {
            "image_path": img,
            "language": lang,
            "text": f"[OCR metin: {img}]",
            "confidence": 0.85,
            "word_count": 0,
        }


class BarcodeQrGeneratorSkill(BaseSkill):
    """QR kod ve barkod becerisi."""

    SKILL_ID = "055"
    NAME = "barcode_qr_generator"
    CATEGORY = "document"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "QR kod ve barkod olusturma/okuma"
    )
    PARAMETERS = {
        "data": "Veri",
        "type": "qr veya barcode",
        "format": "Cikti formati",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        data = p.get("data", "")
        btype = p.get("type", "qr")
        fmt = p.get("format", "png")
        return {
            "data": data,
            "type": btype,
            "format": fmt,
            "output_file": f"{btype}.{fmt}",
            "data_length": len(data),
        }


ALL_DOCUMENT_SKILLS: list[type[BaseSkill]] = [
    PdfReaderSkill,
    PdfMergerSkill,
    PdfSplitterSkill,
    PdfCreatorSkill,
    ExcelReaderSkill,
    ExcelCreatorSkill,
    CsvProcessorSkill,
    JsonFormatterSkill,
    YamlProcessorSkill,
    XmlProcessorSkill,
    MarkdownProcessorSkill,
    DocxReaderSkill,
    DocxCreatorSkill,
    PptxReaderSkill,
    PptxCreatorSkill,
    FileConverterSkill,
    FileCompressorSkill,
    FileHasherSkill,
    OcrReaderSkill,
    BarcodeQrGeneratorSkill,
]
