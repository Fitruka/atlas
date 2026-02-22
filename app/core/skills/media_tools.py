"""Gorsel ve medya becerileri.

Resim, video, ses, grafik islemleri
icin 20 beceri.
"""

import colorsys
import math
from typing import Any

from app.core.skills.base_skill import BaseSkill


class ImageResizerSkill(BaseSkill):
    """Resim boyutlandirma becerisi."""

    SKILL_ID = "056"
    NAME = "image_resizer"
    CATEGORY = "media"
    RISK_LEVEL = "low"
    DESCRIPTION = "Resim boyutlandirma, kirpma"
    PARAMETERS = {
        "image_path": "Resim yolu",
        "width": "Genislik",
        "height": "Yukseklik",
        "mode": "fit/fill/crop",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        w = p.get("width", 800)
        h = p.get("height", 600)
        mode = p.get("mode", "fit")
        return {
            "width": w, "height": h,
            "mode": mode,
            "output": "resized.png",
        }


class ImageCompressorSkill(BaseSkill):
    """Resim sikistirma becerisi."""

    SKILL_ID = "057"
    NAME = "image_compressor"
    CATEGORY = "media"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Resim sikistirma (kalite ayari ile)"
    )
    PARAMETERS = {
        "image_path": "Resim yolu",
        "quality": "Kalite (1-100)",
        "max_size_kb": "Maks boyut KB",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        quality = p.get("quality", 80)
        max_kb = p.get("max_size_kb", 500)
        return {
            "quality": quality,
            "max_size_kb": max_kb,
            "output": "compressed.jpg",
            "reduction_percent": 100 - quality,
        }


class ImageConverterSkill(BaseSkill):
    """Resim format cevirici becerisi."""

    SKILL_ID = "058"
    NAME = "image_converter"
    CATEGORY = "media"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Resim format cevirme "
        "(PNG<->JPG<->WebP<->SVG<->BMP)"
    )
    PARAMETERS = {
        "image_path": "Resim yolu",
        "output_format": "Cikti formati",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        fmt = p.get("output_format", "png")
        return {
            "output_format": fmt,
            "output": f"converted.{fmt}",
        }


class ImageMetadataSkill(BaseSkill):
    """Resim metadata becerisi."""

    SKILL_ID = "059"
    NAME = "image_metadata"
    CATEGORY = "media"
    RISK_LEVEL = "low"
    DESCRIPTION = "EXIF verisi okuma/temizleme"
    PARAMETERS = {
        "image_path": "Resim yolu",
        "operation": "read/strip",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        op = p.get("operation", "read")
        return {
            "operation": op,
            "metadata": {
                "camera": "Unknown",
                "date": "Unknown",
                "resolution": "Unknown",
                "gps": None,
            },
        }


class ImageWatermarkSkill(BaseSkill):
    """Resim filigran becerisi."""

    SKILL_ID = "060"
    NAME = "image_watermark"
    CATEGORY = "media"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Resme filigran ekleme "
        "(metin veya resim)"
    )
    PARAMETERS = {
        "image_path": "Resim yolu",
        "watermark_text": "Filigran metni",
        "position": "Konum",
        "opacity": "Seffaflik (0-1)",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        text = p.get("watermark_text", "ATLAS")
        pos = p.get("position", "center")
        opacity = p.get("opacity", 0.5)
        return {
            "watermark_text": text,
            "position": pos,
            "opacity": opacity,
            "output": "watermarked.png",
        }


class ScreenshotCaptureSkill(BaseSkill):
    """Ekran goruntusu becerisi."""

    SKILL_ID = "061"
    NAME = "screenshot_capture"
    CATEGORY = "media"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "URL'den ekran goruntusu alma"
    )
    PARAMETERS = {
        "url": "Web adresi",
        "device": "desktop/mobile/tablet",
        "full_page": "Tam sayfa mi",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        url = p.get("url", "")
        device = p.get("device", "desktop")
        full = p.get("full_page", True)
        sizes = {
            "desktop": (1920, 1080),
            "mobile": (375, 812),
            "tablet": (768, 1024),
        }
        w, h = sizes.get(device, (1920, 1080))
        return {
            "url": url, "device": device,
            "full_page": full,
            "width": w, "height": h,
            "output": "screenshot.png",
        }


class ColorPickerSkill(BaseSkill):
    """Renk kodu cevirici becerisi."""

    SKILL_ID = "062"
    NAME = "color_picker"
    CATEGORY = "media"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Renk kodu cevirici "
        "(HEX<->RGB<->HSL<->CMYK)"
    )
    PARAMETERS = {
        "color": "Renk degeri",
        "target_format": "Hedef format",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        color = p.get("color", "#FF5733")
        color = color.lstrip("#")

        if len(color) == 6:
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
        else:
            r, g, b = 255, 87, 51

        h, l, s = colorsys.rgb_to_hls(
            r / 255, g / 255, b / 255,
        )
        c = 1 - r / 255
        m = 1 - g / 255
        y = 1 - b / 255
        k = min(c, m, y)

        return {
            "hex": f"#{r:02x}{g:02x}{b:02x}",
            "rgb": {"r": r, "g": g, "b": b},
            "hsl": {
                "h": round(h * 360),
                "s": round(s * 100),
                "l": round(l * 100),
            },
            "cmyk": {
                "c": round(c * 100),
                "m": round(m * 100),
                "y": round(y * 100),
                "k": round(k * 100),
            },
        }


class ColorPaletteSkill(BaseSkill):
    """Renk paleti olusturma becerisi."""

    SKILL_ID = "063"
    NAME = "color_palette"
    CATEGORY = "media"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Uyumlu renk paleti olusturma"
    )
    PARAMETERS = {
        "base_color": "Temel renk (HEX)",
        "scheme_type": "complementary/analogous/triadic",
        "count": "Renk sayisi",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        base = p.get("base_color", "#FF5733")
        scheme = p.get(
            "scheme_type", "complementary",
        )
        count = p.get("count", 5)
        base = base.lstrip("#")

        r = int(base[0:2], 16)
        g = int(base[2:4], 16)
        b = int(base[4:6], 16)
        h, l, s = colorsys.rgb_to_hls(
            r / 255, g / 255, b / 255,
        )

        colors = []
        for i in range(count):
            if scheme == "complementary":
                nh = (h + 0.5 * (i / max(count - 1, 1))) % 1.0
            elif scheme == "analogous":
                nh = (h + 0.083 * (i - count // 2)) % 1.0
            else:
                nh = (h + i / count) % 1.0

            nr, ng, nb = colorsys.hls_to_rgb(
                nh, l, s,
            )
            colors.append(
                f"#{int(nr*255):02x}"
                f"{int(ng*255):02x}"
                f"{int(nb*255):02x}"
            )

        return {
            "base_color": f"#{base}",
            "scheme": scheme,
            "palette": colors,
        }


class FaviconGeneratorSkill(BaseSkill):
    """Favicon olusturma becerisi."""

    SKILL_ID = "064"
    NAME = "favicon_generator"
    CATEGORY = "media"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "URL'den veya resimden "
        "favicon olusturma"
    )
    PARAMETERS = {
        "input": "Kaynak",
        "sizes": "Boyutlar listesi",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        sizes = p.get(
            "sizes", [16, 32, 48, 64, 128],
        )
        outputs = [
            f"favicon-{s}x{s}.png"
            for s in sizes
        ]
        return {
            "sizes": sizes,
            "outputs": outputs,
            "ico_file": "favicon.ico",
        }


class ImageToAsciiSkill(BaseSkill):
    """ASCII art cevirici becerisi."""

    SKILL_ID = "065"
    NAME = "image_to_ascii"
    CATEGORY = "media"
    RISK_LEVEL = "low"
    DESCRIPTION = "Resmi ASCII art'a cevirme"
    PARAMETERS = {
        "image_path": "Resim yolu",
        "width": "Genislik (karakter)",
        "charset": "Karakter seti",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        width = p.get("width", 80)
        charset = p.get(
            "charset", "@%#*+=-:. ",
        )
        lines = []
        for y in range(width // 2):
            line = ""
            for x in range(width):
                idx = (x + y) % len(charset)
                line += charset[idx]
            lines.append(line)
        return {
            "ascii_art": "\n".join(lines[:20]),
            "width": width,
            "height": len(lines),
        }


class MemeGeneratorSkill(BaseSkill):
    """Meme olusturma becerisi."""

    SKILL_ID = "066"
    NAME = "meme_generator"
    CATEGORY = "media"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Meme sablonlarina metin ekleme"
    )
    PARAMETERS = {
        "template": "Sablon adi",
        "top_text": "Ust metin",
        "bottom_text": "Alt metin",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        template = p.get(
            "template", "drake",
        )
        top = p.get("top_text", "")
        bottom = p.get("bottom_text", "")
        return {
            "template": template,
            "top_text": top,
            "bottom_text": bottom,
            "output": f"meme_{template}.png",
        }


class ChartGeneratorSkill(BaseSkill):
    """Grafik olusturma becerisi."""

    SKILL_ID = "067"
    NAME = "chart_generator"
    CATEGORY = "media"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Veri gorsellestirme "
        "(bar, pie, line, scatter, heatmap)"
    )
    PARAMETERS = {
        "data": "Veri",
        "chart_type": "Grafik tipi",
        "title": "Baslik",
        "labels": "Etiketler",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        data = p.get("data", {})
        ctype = p.get("chart_type", "bar")
        title = p.get("title", "Chart")
        return {
            "chart_type": ctype,
            "title": title,
            "data_points": (
                len(data) if isinstance(
                    data, (list, dict),
                ) else 0
            ),
            "output": f"{ctype}_chart.png",
        }


class DiagramGeneratorSkill(BaseSkill):
    """Diagram olusturma becerisi."""

    SKILL_ID = "068"
    NAME = "diagram_generator"
    CATEGORY = "media"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Akis semasi, mind map, "
        "organizasyon semasi (Mermaid)"
    )
    PARAMETERS = {
        "type": "Diagram tipi",
        "nodes": "Dugumler",
        "connections": "Baglantilar",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        dtype = p.get("type", "flowchart")
        nodes = p.get("nodes", [])
        conns = p.get("connections", [])

        mermaid = f"graph TD\n"
        for i, node in enumerate(nodes):
            mermaid += f"    N{i}[{node}]\n"
        for conn in conns:
            if len(conn) >= 2:
                mermaid += (
                    f"    N{conn[0]} --> "
                    f"N{conn[1]}\n"
                )

        return {
            "type": dtype,
            "mermaid": mermaid,
            "node_count": len(nodes),
            "connection_count": len(conns),
        }


class SvgCreatorSkill(BaseSkill):
    """SVG olusturma becerisi."""

    SKILL_ID = "069"
    NAME = "svg_creator"
    CATEGORY = "media"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "SVG ikon ve basit grafik olusturma"
    )
    PARAMETERS = {
        "shape": "Sekil (circle/rect/line)",
        "size": "Boyut",
        "color": "Renk",
        "text": "Metin",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        shape = p.get("shape", "circle")
        size = p.get("size", 100)
        color = p.get("color", "#3498db")
        text = p.get("text", "")

        svg = f'<svg width="{size}" height="{size}">\n'
        if shape == "circle":
            r = size // 2
            svg += (
                f'  <circle cx="{r}" cy="{r}" '
                f'r="{r}" fill="{color}"/>\n'
            )
        elif shape == "rect":
            svg += (
                f'  <rect width="{size}" '
                f'height="{size}" '
                f'fill="{color}"/>\n'
            )
        if text:
            svg += (
                f'  <text x="50%" y="50%" '
                f'text-anchor="middle">'
                f'{text}</text>\n'
            )
        svg += "</svg>"

        return {
            "shape": shape, "size": size,
            "color": color, "svg": svg,
        }


class GifCreatorSkill(BaseSkill):
    """GIF olusturma becerisi."""

    SKILL_ID = "070"
    NAME = "gif_creator"
    CATEGORY = "media"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Resimlerden GIF animasyon olusturma"
    )
    PARAMETERS = {
        "images": "Resim listesi",
        "delay": "Kare arasi gecikme (ms)",
        "loop": "Dongu sayisi",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        images = p.get("images", [])
        delay = p.get("delay", 100)
        loop = p.get("loop", 0)
        return {
            "frame_count": len(images),
            "delay_ms": delay,
            "loop": loop,
            "output": "animation.gif",
        }


class VideoThumbnailSkill(BaseSkill):
    """Video thumbnail becerisi."""

    SKILL_ID = "071"
    NAME = "video_thumbnail"
    CATEGORY = "media"
    RISK_LEVEL = "low"
    DESCRIPTION = "Video'dan thumbnail cikarma"
    PARAMETERS = {
        "video_path": "Video yolu",
        "timestamp": "Zaman damgasi (sn)",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        ts = p.get("timestamp", 0)
        return {
            "timestamp": ts,
            "output": "thumbnail.jpg",
        }


class AudioTranscriberSkill(BaseSkill):
    """Ses transkripsiyon becerisi."""

    SKILL_ID = "072"
    NAME = "audio_transcriber"
    CATEGORY = "media"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Ses dosyasindan metin cikarma "
        "(Whisper)"
    )
    PARAMETERS = {
        "audio_path": "Ses dosya yolu",
        "language": "Dil",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        lang = p.get("language", "tr")
        return {
            "language": lang,
            "text": "[Transkripsiyon sonucu]",
            "duration_seconds": 0,
            "confidence": 0.90,
        }


class TextToSpeechSkill(BaseSkill):
    """Metinden sese cevirme becerisi."""

    SKILL_ID = "073"
    NAME = "text_to_speech"
    CATEGORY = "media"
    RISK_LEVEL = "low"
    DESCRIPTION = "Metni sese cevirme"
    PARAMETERS = {
        "text": "Metin",
        "voice": "Ses",
        "language": "Dil",
        "speed": "Hiz (0.5-2.0)",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        text = p.get("text", "")
        voice = p.get("voice", "default")
        lang = p.get("language", "tr")
        speed = p.get("speed", 1.0)
        dur = len(text.split()) * 0.4 / speed
        return {
            "text_length": len(text),
            "voice": voice, "language": lang,
            "speed": speed,
            "estimated_duration": round(dur, 1),
            "output": "speech.mp3",
        }


class AudioConverterSkill(BaseSkill):
    """Ses format cevirici becerisi."""

    SKILL_ID = "074"
    NAME = "audio_converter"
    CATEGORY = "media"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Ses format cevirme "
        "(mp3<->wav<->ogg<->flac)"
    )
    PARAMETERS = {
        "audio_path": "Ses dosya yolu",
        "output_format": "Cikti formati",
        "bitrate": "Bit hizi",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        fmt = p.get("output_format", "mp3")
        bitrate = p.get("bitrate", "128k")
        return {
            "output_format": fmt,
            "bitrate": bitrate,
            "output": f"audio.{fmt}",
        }


class VideoConverterSkill(BaseSkill):
    """Video format cevirici becerisi."""

    SKILL_ID = "075"
    NAME = "video_converter"
    CATEGORY = "media"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Video format cevirme, sikistirma"
    )
    PARAMETERS = {
        "video_path": "Video yolu",
        "output_format": "Cikti formati",
        "quality": "Kalite",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        fmt = p.get("output_format", "mp4")
        quality = p.get("quality", "medium")
        return {
            "output_format": fmt,
            "quality": quality,
            "output": f"video.{fmt}",
        }


ALL_MEDIA_SKILLS: list[type[BaseSkill]] = [
    ImageResizerSkill,
    ImageCompressorSkill,
    ImageConverterSkill,
    ImageMetadataSkill,
    ImageWatermarkSkill,
    ScreenshotCaptureSkill,
    ColorPickerSkill,
    ColorPaletteSkill,
    FaviconGeneratorSkill,
    ImageToAsciiSkill,
    MemeGeneratorSkill,
    ChartGeneratorSkill,
    DiagramGeneratorSkill,
    SvgCreatorSkill,
    GifCreatorSkill,
    VideoThumbnailSkill,
    AudioTranscriberSkill,
    TextToSpeechSkill,
    AudioConverterSkill,
    VideoConverterSkill,
]
