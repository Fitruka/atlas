"""
Veri Analiz & Bilim becerileri (226-250).

Istatistik, olasilik, matris, regresyon, kumeleme, zaman serisi, huni analizi,
musteri segmentasyonu ve birim ekonomi araclari.
"""

from __future__ import annotations

import math
import random
import hashlib
from collections import Counter
from typing import Any

from app.core.skills.base_skill import BaseSkill


# ── Yardimci fonksiyonlar ──────────────────────────────────────────────────

def _mean(data: list[float]) -> float:
    return sum(data) / len(data) if data else 0.0


def _median(data: list[float]) -> float:
    s = sorted(data)
    n = len(s)
    if n == 0:
        return 0.0
    mid = n // 2
    return (s[mid - 1] + s[mid]) / 2 if n % 2 == 0 else s[mid]


def _variance(data: list[float], ddof: int = 0) -> float:
    if len(data) < 2:
        return 0.0
    m = _mean(data)
    return sum((x - m) ** 2 for x in data) / (len(data) - ddof)


def _std(data: list[float], ddof: int = 0) -> float:
    return math.sqrt(_variance(data, ddof))


def _percentile(data: list[float], p: float) -> float:
    s = sorted(data)
    n = len(s)
    if n == 0:
        return 0.0
    k = (n - 1) * (p / 100)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return s[int(k)]
    return s[f] * (c - k) + s[c] * (k - f)


def _correlation(x: list[float], y: list[float]) -> float:
    n = min(len(x), len(y))
    if n < 2:
        return 0.0
    mx, my = _mean(x[:n]), _mean(y[:n])
    num = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    dx = math.sqrt(sum((x[i] - mx) ** 2 for i in range(n)))
    dy = math.sqrt(sum((y[i] - my) ** 2 for i in range(n)))
    if dx == 0 or dy == 0:
        return 0.0
    return num / (dx * dy)


def _factorial(n: int) -> int:
    if n <= 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def _combination(n: int, r: int) -> int:
    if r > n or r < 0:
        return 0
    return _factorial(n) // (_factorial(r) * _factorial(n - r))


def _permutation(n: int, r: int) -> int:
    if r > n or r < 0:
        return 0
    return _factorial(n) // _factorial(n - r)


def _to_float_list(data: Any) -> list[float]:
    """Veriyi float listesine cevir."""
    if isinstance(data, (list, tuple)):
        return [float(x) for x in data if x is not None]
    if isinstance(data, str):
        parts = data.replace(";", ",").split(",")
        return [float(x.strip()) for x in parts if x.strip()]
    return []


# ────────────────────────────────────────────────────────────────────────────
# 226 — statistics_calculator
# ────────────────────────────────────────────────────────────────────────────
class StatisticsCalculator(BaseSkill):
    """Istatistik hesaplama."""

    SKILL_ID = "226"
    NAME = "statistics_calculator"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "Istatistik hesaplama (ortalama, medyan, std sapma, percentil, korelasyon)"
    PARAMETERS = {
        "data": "Veri dizisi (virgul ile ayrilmis sayilar veya dizi)",
        "operation": "Islem (summary/mean/median/std/percentile/correlation/all)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        raw = params.get("data", [])
        operation = str(params.get("operation", "all")).lower()
        data = _to_float_list(raw)

        if not data:
            return {"status": "error", "message": "Veri gerekli"}

        n = len(data)
        result: dict[str, Any] = {"status": "success", "n": n, "data_preview": data[:20]}

        if operation in ("mean", "all", "summary"):
            result["mean"] = round(_mean(data), 6)
        if operation in ("median", "all", "summary"):
            result["median"] = round(_median(data), 6)
        if operation in ("std", "all", "summary"):
            result["std_population"] = round(_std(data, 0), 6)
            result["std_sample"] = round(_std(data, 1), 6)
            result["variance"] = round(_variance(data, 1), 6)
        if operation in ("percentile", "all", "summary"):
            result["percentiles"] = {
                "p25": round(_percentile(data, 25), 4),
                "p50": round(_percentile(data, 50), 4),
                "p75": round(_percentile(data, 75), 4),
                "p90": round(_percentile(data, 90), 4),
                "p95": round(_percentile(data, 95), 4),
                "p99": round(_percentile(data, 99), 4),
            }
        if operation in ("all", "summary"):
            result["min"] = min(data)
            result["max"] = max(data)
            result["range"] = round(max(data) - min(data), 6)
            result["sum"] = round(sum(data), 6)
            # Mode
            counter = Counter(data)
            most_common = counter.most_common(1)
            result["mode"] = most_common[0][0] if most_common and most_common[0][1] > 1 else None
            # Skewness (Fisher)
            m = _mean(data)
            s = _std(data, 1) or 1
            result["skewness"] = round(sum(((x - m) / s) ** 3 for x in data) * n / ((n - 1) * (n - 2)) if n > 2 else 0, 4)

        return result


# ────────────────────────────────────────────────────────────────────────────
# 227 — probability_calculator
# ────────────────────────────────────────────────────────────────────────────
class ProbabilityCalculator(BaseSkill):
    """Olasilik hesaplama."""

    SKILL_ID = "227"
    NAME = "probability_calculator"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "Olasilik hesaplama (kombinasyon, permutasyon, Bayes)"
    PARAMETERS = {
        "type": "Hesap tipi (combination/permutation/bayes/binomial/independent)",
        "parameters": "Parametreler (dict veya comma-separated)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        calc_type = str(params.get("type", "combination")).lower()
        p = params.get("parameters", {})
        if isinstance(p, str):
            parts = p.split(",")
            p = {"values": [float(x.strip()) for x in parts if x.strip()]}

        if calc_type == "combination":
            n = int(p.get("n", p.get("values", [10, 3])[0] if "values" in p else 10))
            r = int(p.get("r", p.get("values", [10, 3])[1] if "values" in p and len(p["values"]) > 1 else 3))
            result = _combination(n, r)
            return {"status": "success", "type": "combination", "n": n, "r": r,
                    "C(n,r)": result, "formula": f"C({n},{r}) = {n}! / ({r}! * {n - r}!)"}

        if calc_type == "permutation":
            n = int(p.get("n", 10))
            r = int(p.get("r", 3))
            result = _permutation(n, r)
            return {"status": "success", "type": "permutation", "n": n, "r": r,
                    "P(n,r)": result, "formula": f"P({n},{r}) = {n}! / {n - r}!"}

        if calc_type == "bayes":
            prior = float(p.get("prior", p.get("P_A", 0.01)))
            likelihood = float(p.get("likelihood", p.get("P_B_given_A", 0.9)))
            marginal = float(p.get("marginal", p.get("P_B", 0.05)))
            if marginal == 0:
                return {"status": "error", "message": "P(B) sifir olamaz"}
            posterior = (likelihood * prior) / marginal
            return {
                "status": "success", "type": "bayes",
                "P_A": prior, "P_B_given_A": likelihood, "P_B": marginal,
                "P_A_given_B": round(posterior, 6),
                "formula": "P(A|B) = P(B|A) * P(A) / P(B)",
            }

        if calc_type == "binomial":
            n = int(p.get("n", 10))
            k = int(p.get("k", 3))
            prob = float(p.get("p", 0.5))
            binom = _combination(n, k) * (prob ** k) * ((1 - prob) ** (n - k))
            return {
                "status": "success", "type": "binomial",
                "n": n, "k": k, "p": prob,
                "probability": round(binom, 8),
                "expected_value": round(n * prob, 4),
                "std_dev": round(math.sqrt(n * prob * (1 - prob)), 4),
            }

        if calc_type == "independent":
            probs = _to_float_list(p.get("probabilities", p.get("values", [0.5, 0.5])))
            combined = 1.0
            for pr in probs:
                combined *= pr
            at_least_one = 1 - combined
            none_prob = 1.0
            for pr in probs:
                none_prob *= (1 - pr)
            return {
                "status": "success", "type": "independent_events",
                "probabilities": probs,
                "all_occur": round(combined, 8),
                "none_occur": round(none_prob, 8),
                "at_least_one": round(1 - none_prob, 8),
            }

        return {"status": "error", "message": f"Bilinmeyen tip: {calc_type}",
                "valid_types": ["combination", "permutation", "bayes", "binomial", "independent"]}


# ────────────────────────────────────────────────────────────────────────────
# 228 — matrix_calculator
# ────────────────────────────────────────────────────────────────────────────
class MatrixCalculator(BaseSkill):
    """Matris islemleri."""

    SKILL_ID = "228"
    NAME = "matrix_calculator"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "Matris islemleri (carpma, determinant, ters matris)"
    PARAMETERS = {
        "matrices": "Matrisler (2D diziler)",
        "operation": "Islem (add/subtract/multiply/determinant/inverse/transpose)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        matrices = params.get("matrices", [])
        operation = str(params.get("operation", "determinant")).lower()

        if not matrices:
            matrices = [[[1, 2], [3, 4]]]

        if isinstance(matrices, list) and matrices and isinstance(matrices[0], list):
            if isinstance(matrices[0][0], (int, float)):
                matrices = [matrices]  # Tek matris

        a = matrices[0] if len(matrices) > 0 else [[1, 0], [0, 1]]
        b = matrices[1] if len(matrices) > 1 else None
        rows_a = len(a)
        cols_a = len(a[0]) if a else 0

        if operation == "transpose":
            t = [[a[r][c] for r in range(rows_a)] for c in range(cols_a)]
            return {"status": "success", "operation": "transpose", "original": a, "result": t}

        if operation == "determinant":
            if rows_a != cols_a:
                return {"status": "error", "message": "Kare matris gerekli"}
            if rows_a == 2:
                det = a[0][0] * a[1][1] - a[0][1] * a[1][0]
            elif rows_a == 3:
                det = (a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1])
                       - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
                       + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0]))
            else:
                det = 0  # Sadece 2x2 ve 3x3 destekliyoruz
            return {"status": "success", "operation": "determinant", "matrix": a, "determinant": det}

        if operation == "inverse":
            if rows_a != cols_a:
                return {"status": "error", "message": "Kare matris gerekli"}
            if rows_a == 2:
                det = a[0][0] * a[1][1] - a[0][1] * a[1][0]
                if det == 0:
                    return {"status": "error", "message": "Matris tersinemez (det=0)"}
                inv = [
                    [round(a[1][1] / det, 6), round(-a[0][1] / det, 6)],
                    [round(-a[1][0] / det, 6), round(a[0][0] / det, 6)],
                ]
                return {"status": "success", "operation": "inverse", "matrix": a,
                        "determinant": det, "inverse": inv}
            return {"status": "error", "message": "Ters matris sadece 2x2 icin destekleniyor"}

        if operation in ("add", "subtract"):
            if b is None:
                return {"status": "error", "message": "Iki matris gerekli"}
            rows_b, cols_b = len(b), len(b[0]) if b else 0
            if rows_a != rows_b or cols_a != cols_b:
                return {"status": "error", "message": "Matris boyutlari uyusmuyor"}
            sign = 1 if operation == "add" else -1
            result = [[a[r][c] + sign * b[r][c] for c in range(cols_a)] for r in range(rows_a)]
            return {"status": "success", "operation": operation, "A": a, "B": b, "result": result}

        if operation == "multiply":
            if b is None:
                return {"status": "error", "message": "Iki matris gerekli"}
            rows_b, cols_b = len(b), len(b[0]) if b else 0
            if cols_a != rows_b:
                return {"status": "error", "message": f"A sutun ({cols_a}) != B satir ({rows_b})"}
            result = [[sum(a[r][k] * b[k][c] for k in range(cols_a)) for c in range(cols_b)] for r in range(rows_a)]
            return {"status": "success", "operation": "multiply", "A": a, "B": b, "result": result,
                    "dimensions": f"{rows_a}x{cols_b}"}

        return {"status": "error", "message": f"Bilinmeyen islem: {operation}"}


# ────────────────────────────────────────────────────────────────────────────
# 229 — equation_solver
# ────────────────────────────────────────────────────────────────────────────
class EquationSolver(BaseSkill):
    """Denklem cozucu."""

    SKILL_ID = "229"
    NAME = "equation_solver"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "Denklem cozucu (lineer, kuadratik)"
    PARAMETERS = {
        "equation": "Denklem (ornek: '2x + 3 = 7' veya 'x^2 - 5x + 6 = 0')",
        "variable": "Degisken (varsayilan x)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        equation = str(params.get("equation", ""))
        variable = str(params.get("variable", "x"))

        # Kuadratik: a, b, c parametreleri (equation gerektirmez)
        a = params.get("a")
        b_param = params.get("b")
        c = params.get("c")

        if not equation and a is None:
            return {"status": "error", "message": "Denklem gerekli"}

        if a is not None and b_param is not None and c is not None:
            a, b_val, c = float(a), float(b_param), float(c)
            discriminant = b_val ** 2 - 4 * a * c
            if discriminant > 0:
                x1 = (-b_val + math.sqrt(discriminant)) / (2 * a)
                x2 = (-b_val - math.sqrt(discriminant)) / (2 * a)
                return {"status": "success", "type": "quadratic",
                        "equation": f"{a}{variable}² + {b_val}{variable} + {c} = 0",
                        "discriminant": discriminant, "roots": [round(x1, 6), round(x2, 6)]}
            elif discriminant == 0:
                x1 = -b_val / (2 * a)
                return {"status": "success", "type": "quadratic",
                        "equation": f"{a}{variable}² + {b_val}{variable} + {c} = 0",
                        "discriminant": 0, "roots": [round(x1, 6)], "note": "Cift kok"}
            else:
                real = -b_val / (2 * a)
                imag = math.sqrt(-discriminant) / (2 * a)
                return {"status": "success", "type": "quadratic",
                        "discriminant": discriminant,
                        "roots": [f"{round(real, 4)} + {round(imag, 4)}i",
                                  f"{round(real, 4)} - {round(imag, 4)}i"],
                        "note": "Kompleks kokler"}

        # Basit lineer denklem parse: ax + b = c
        eq = equation.replace(" ", "")
        if "=" in eq:
            left, right = eq.split("=", 1)
            try:
                right_val = float(right)
            except ValueError:
                right_val = 0

            # ax + b formati
            if variable in left:
                # Katsayi ve sabit bul
                left = left.replace("-", "+-")
                terms = [t for t in left.split("+") if t]
                coeff = 0.0
                constant = 0.0
                for term in terms:
                    if variable in term:
                        c_str = term.replace(variable, "").replace("^1", "")
                        coeff = float(c_str) if c_str and c_str != "+" and c_str != "-" else (1.0 if "-" not in c_str else -1.0)
                    else:
                        try:
                            constant += float(term)
                        except ValueError:
                            pass

                if coeff == 0:
                    return {"status": "error", "message": "Degisken katsayisi sifir"}

                solution = (right_val - constant) / coeff
                return {"status": "success", "type": "linear",
                        "equation": equation, "variable": variable,
                        "solution": round(solution, 6)}

        return {"status": "error", "message": "Denklem parse edilemedi. Ornek: '2x + 3 = 7'"}


# ────────────────────────────────────────────────────────────────────────────
# 230 — graph_plotter
# ────────────────────────────────────────────────────────────────────────────
class GraphPlotter(BaseSkill):
    """Matematiksel fonksiyon grafigi cizme (ASCII)."""

    SKILL_ID = "230"
    NAME = "graph_plotter"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "Matematiksel fonksiyon grafigi cizme"
    PARAMETERS = {
        "function": "Fonksiyon (sin/cos/linear/quadratic/exponential)",
        "x_range": "X araligi (min,max)",
        "y_range": "Y araligi (min,max)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        func_name = str(params.get("function", "sin")).lower()
        x_range = params.get("x_range", [-10, 10])
        if isinstance(x_range, str):
            parts = x_range.split(",")
            x_range = [float(parts[0]), float(parts[1])] if len(parts) >= 2 else [-10, 10]

        x_min, x_max = float(x_range[0]), float(x_range[1])
        points = 50

        func_map = {
            "sin": math.sin,
            "cos": math.cos,
            "linear": lambda x: x,
            "quadratic": lambda x: x ** 2,
            "exponential": lambda x: min(math.exp(x / 5), 1e6),
            "sqrt": lambda x: math.sqrt(abs(x)),
            "log": lambda x: math.log(abs(x) + 0.001),
        }

        func = func_map.get(func_name, math.sin)
        step = (x_max - x_min) / points

        data_points: list[dict[str, float]] = []
        y_values: list[float] = []
        for i in range(points + 1):
            x = x_min + i * step
            try:
                y = func(x)
                if math.isfinite(y):
                    data_points.append({"x": round(x, 4), "y": round(y, 4)})
                    y_values.append(y)
            except (ValueError, OverflowError):
                pass

        # ASCII grafik
        if y_values:
            y_min_actual = min(y_values)
            y_max_actual = max(y_values)
            height = 15
            width = min(50, len(data_points))

            ascii_art = []
            for row in range(height, -1, -1):
                line = ""
                y_val = y_min_actual + (y_max_actual - y_min_actual) * row / height
                for col in range(width):
                    idx = col * len(data_points) // width
                    if idx < len(data_points):
                        py = data_points[idx]["y"]
                        py_row = int((py - y_min_actual) / (y_max_actual - y_min_actual + 1e-10) * height)
                        if py_row == row:
                            line += "*"
                        elif row == 0:
                            line += "-"
                        elif col == 0:
                            line += "|"
                        else:
                            line += " "
                    else:
                        line += " "
                ascii_art.append(line)
        else:
            ascii_art = ["Grafik uretilemedi"]

        return {
            "status": "success",
            "function": func_name,
            "x_range": [x_min, x_max],
            "y_range": [round(min(y_values), 4), round(max(y_values), 4)] if y_values else [0, 0],
            "data_points_count": len(data_points),
            "data_points": data_points[:20],
            "ascii_graph": "\n".join(ascii_art),
        }


# ────────────────────────────────────────────────────────────────────────────
# 231 — data_cleaner
# ────────────────────────────────────────────────────────────────────────────
class DataCleaner(BaseSkill):
    """Veri temizleme."""

    SKILL_ID = "231"
    NAME = "data_cleaner"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "Veri temizleme (duplikat, bos deger, format duzeltme)"
    PARAMETERS = {
        "data": "Veri (dizi veya dict dizisi)",
        "operations": "Islemler (remove_duplicates/fill_nulls/trim/lowercase/remove_outliers)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        data = params.get("data", [])
        operations = params.get("operations", "remove_duplicates,fill_nulls,trim")
        if isinstance(operations, str):
            operations = [o.strip() for o in operations.split(",")]

        if not data:
            return {"status": "error", "message": "Veri gerekli"}

        original_count = len(data) if isinstance(data, list) else 0
        cleaned = list(data) if isinstance(data, list) else [data]
        changes: list[str] = []

        if "remove_duplicates" in operations:
            if all(isinstance(x, (int, float, str)) for x in cleaned):
                before = len(cleaned)
                seen: set[Any] = set()
                unique: list[Any] = []
                for item in cleaned:
                    if item not in seen:
                        seen.add(item)
                        unique.append(item)
                cleaned = unique
                removed = before - len(cleaned)
                if removed:
                    changes.append(f"{removed} duplikat kaldirildi")

        if "fill_nulls" in operations:
            filled = 0
            for i in range(len(cleaned)):
                if cleaned[i] is None or cleaned[i] == "" or cleaned[i] == "null":
                    cleaned[i] = 0 if all(isinstance(x, (int, float)) for x in cleaned if x is not None) else "N/A"
                    filled += 1
            if filled:
                changes.append(f"{filled} bos deger dolduruldu")

        if "trim" in operations:
            trimmed = 0
            for i in range(len(cleaned)):
                if isinstance(cleaned[i], str):
                    new = cleaned[i].strip()
                    if new != cleaned[i]:
                        cleaned[i] = new
                        trimmed += 1
            if trimmed:
                changes.append(f"{trimmed} deger kirpildi")

        if "lowercase" in operations:
            lower_count = 0
            for i in range(len(cleaned)):
                if isinstance(cleaned[i], str):
                    new = cleaned[i].lower()
                    if new != cleaned[i]:
                        cleaned[i] = new
                        lower_count += 1
            if lower_count:
                changes.append(f"{lower_count} deger kucuk harfe cevirildi")

        if "remove_outliers" in operations:
            numeric = [x for x in cleaned if isinstance(x, (int, float))]
            if len(numeric) > 3:
                q1 = _percentile(numeric, 25)
                q3 = _percentile(numeric, 75)
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                before = len(cleaned)
                cleaned = [x for x in cleaned if not isinstance(x, (int, float)) or (lower <= x <= upper)]
                removed = before - len(cleaned)
                if removed:
                    changes.append(f"{removed} outlier kaldirildi (IQR yontemi)")

        return {
            "status": "success",
            "original_count": original_count,
            "cleaned_count": len(cleaned),
            "changes": changes,
            "cleaned_data_preview": cleaned[:20],
        }


# ────────────────────────────────────────────────────────────────────────────
# 232 — data_profiler
# ────────────────────────────────────────────────────────────────────────────
class DataProfiler(BaseSkill):
    """Veri seti profilleme."""

    SKILL_ID = "232"
    NAME = "data_profiler"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "Veri seti profilleme (tip, dagilim, eksik, outlier)"
    PARAMETERS = {"data": "Veri (dizi veya dict dizisi)"}

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        data = params.get("data", params.get("data_file", []))
        if not data:
            return {"status": "error", "message": "Veri gerekli"}

        if isinstance(data, list) and data and isinstance(data[0], dict):
            # Dict dizisi profilleme
            columns: dict[str, dict[str, Any]] = {}
            n_rows = len(data)
            for col in data[0].keys():
                values = [row.get(col) for row in data]
                non_null = [v for v in values if v is not None and v != ""]
                numeric = [float(v) for v in non_null if isinstance(v, (int, float))]

                profile: dict[str, Any] = {
                    "count": len(values),
                    "non_null": len(non_null),
                    "null_count": len(values) - len(non_null),
                    "null_pct": round((len(values) - len(non_null)) / max(len(values), 1) * 100, 1),
                    "unique": len(set(str(v) for v in non_null)),
                }
                if numeric:
                    profile["type"] = "numeric"
                    profile["mean"] = round(_mean(numeric), 4)
                    profile["median"] = round(_median(numeric), 4)
                    profile["std"] = round(_std(numeric, 1), 4)
                    profile["min"] = min(numeric)
                    profile["max"] = max(numeric)
                else:
                    profile["type"] = "text"
                    if non_null:
                        profile["avg_length"] = round(_mean([len(str(v)) for v in non_null]), 1)
                        top = Counter(str(v) for v in non_null).most_common(3)
                        profile["top_values"] = [{"value": v, "count": c} for v, c in top]

                columns[col] = profile

            return {"status": "success", "rows": n_rows, "columns_count": len(columns), "columns": columns}

        # Basit liste profilleme
        if isinstance(data, list):
            numeric = [float(x) for x in data if isinstance(x, (int, float))]
            text = [str(x) for x in data if isinstance(x, str)]
            return {
                "status": "success",
                "total": len(data),
                "numeric_count": len(numeric),
                "text_count": len(text),
                "null_count": sum(1 for x in data if x is None),
                "unique": len(set(str(x) for x in data)),
                "stats": {
                    "mean": round(_mean(numeric), 4) if numeric else None,
                    "median": round(_median(numeric), 4) if numeric else None,
                    "std": round(_std(numeric, 1), 4) if numeric else None,
                    "min": min(numeric) if numeric else None,
                    "max": max(numeric) if numeric else None,
                },
            }

        return {"status": "error", "message": "Desteklenmeyen veri formati"}


# ────────────────────────────────────────────────────────────────────────────
# 233 — pivot_table
# ────────────────────────────────────────────────────────────────────────────
class PivotTable(BaseSkill):
    """Pivot tablo olusturma."""

    SKILL_ID = "233"
    NAME = "pivot_table"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "Pivot tablo olusturma"
    PARAMETERS = {
        "data": "Veri (dict dizisi)",
        "rows": "Satir alani",
        "columns": "Sutun alani (opsiyonel)",
        "values": "Deger alani",
        "aggregation": "Toplama yontemi (sum/mean/count/min/max)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        data = params.get("data", [])
        rows_field = str(params.get("rows", ""))
        cols_field = str(params.get("columns", ""))
        values_field = str(params.get("values", ""))
        agg = str(params.get("aggregation", "sum")).lower()

        if not data or not isinstance(data, list):
            return {"status": "error", "message": "Dict dizisi verisi gerekli"}

        if not rows_field:
            return {"status": "error", "message": "'rows' alani gerekli"}

        # Gruplama
        groups: dict[str, dict[str, list[float]]] = {}
        for row in data:
            if not isinstance(row, dict):
                continue
            row_key = str(row.get(rows_field, "N/A"))
            col_key = str(row.get(cols_field, "total")) if cols_field else "total"
            val = row.get(values_field, 0)
            try:
                val = float(val)
            except (ValueError, TypeError):
                val = 0

            if row_key not in groups:
                groups[row_key] = {}
            if col_key not in groups[row_key]:
                groups[row_key][col_key] = []
            groups[row_key][col_key].append(val)

        # Toplama
        agg_funcs = {
            "sum": sum, "mean": _mean, "count": len,
            "min": min, "max": max,
        }
        func = agg_funcs.get(agg, sum)

        pivot: dict[str, dict[str, float]] = {}
        for row_key, cols in groups.items():
            pivot[row_key] = {}
            for col_key, values in cols.items():
                pivot[row_key][col_key] = round(func(values), 4)

        return {
            "status": "success",
            "rows_field": rows_field,
            "columns_field": cols_field or None,
            "values_field": values_field,
            "aggregation": agg,
            "pivot_table": pivot,
            "row_count": len(pivot),
        }


# ────────────────────────────────────────────────────────────────────────────
# 234 — correlation_finder
# ────────────────────────────────────────────────────────────────────────────
class CorrelationFinder(BaseSkill):
    """Degiskenler arasi korelasyon analizi."""

    SKILL_ID = "234"
    NAME = "correlation_finder"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "Degiskenler arasi korelasyon analizi"
    PARAMETERS = {
        "data": "Veri (iki veya daha fazla sayisal dizi)",
        "variables": "Degisken isimleri",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        data = params.get("data", {})
        variables = params.get("variables", [])

        if isinstance(data, dict):
            # {"x": [...], "y": [...]}
            var_names = list(data.keys()) if not variables else (variables if isinstance(variables, list) else [variables])
            series = {k: _to_float_list(v) for k, v in data.items() if k in var_names or not variables}
        elif isinstance(data, list) and len(data) >= 2:
            if isinstance(data[0], list):
                var_names = [f"var_{i}" for i in range(len(data))]
                series = {var_names[i]: _to_float_list(data[i]) for i in range(len(data))}
            else:
                return {"status": "error", "message": "Iki veya daha fazla dizi gerekli"}
        else:
            return {"status": "error", "message": "Veri formati: dict veya list of lists"}

        names = list(series.keys())
        if len(names) < 2:
            return {"status": "error", "message": "En az 2 degisken gerekli"}

        corr_matrix: dict[str, dict[str, float]] = {}
        for a_name in names:
            corr_matrix[a_name] = {}
            for b_name in names:
                r = _correlation(series[a_name], series[b_name])
                corr_matrix[a_name][b_name] = round(r, 4)

        # En guclu korelasyonlar
        pairs: list[dict[str, Any]] = []
        for i, a_name in enumerate(names):
            for j, b_name in enumerate(names):
                if i < j:
                    r = corr_matrix[a_name][b_name]
                    strength = "guclu" if abs(r) > 0.7 else ("orta" if abs(r) > 0.4 else "zayif")
                    direction = "pozitif" if r > 0 else "negatif"
                    pairs.append({"var_a": a_name, "var_b": b_name, "correlation": r,
                                  "strength": strength, "direction": direction})

        pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)

        return {
            "status": "success",
            "variables": names,
            "correlation_matrix": corr_matrix,
            "strongest_pairs": pairs[:5],
            "note": "Korelasyon nedensellik anlamina gelmez.",
        }


# ────────────────────────────────────────────────────────────────────────────
# 235 — regression_analyzer
# ────────────────────────────────────────────────────────────────────────────
class RegressionAnalyzer(BaseSkill):
    """Basit regresyon analizi."""

    SKILL_ID = "235"
    NAME = "regression_analyzer"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "Basit/coklu regresyon analizi"
    PARAMETERS = {
        "data": "Veri",
        "dependent_var": "Bagimli degisken",
        "independent_vars": "Bagimsiz degiskenler",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        data = params.get("data", {})
        dep_var = str(params.get("dependent_var", "y"))
        indep = params.get("independent_vars", ["x"])
        if isinstance(indep, str):
            indep = [indep]

        # Basit lineer regresyon: y = mx + b
        if isinstance(data, dict):
            y = _to_float_list(data.get(dep_var, []))
            x = _to_float_list(data.get(indep[0], []))
        elif isinstance(data, list) and len(data) >= 2:
            x = _to_float_list(data[0])
            y = _to_float_list(data[1])
        else:
            return {"status": "error", "message": "Veri gerekli"}

        n = min(len(x), len(y))
        if n < 2:
            return {"status": "error", "message": "En az 2 veri noktasi gerekli"}

        x, y = x[:n], y[:n]
        mx, my = _mean(x), _mean(y)

        ss_xy = sum((x[i] - mx) * (y[i] - my) for i in range(n))
        ss_xx = sum((x[i] - mx) ** 2 for i in range(n))

        if ss_xx == 0:
            return {"status": "error", "message": "X degiskeni sabit"}

        slope = ss_xy / ss_xx
        intercept = my - slope * mx

        # R-squared
        y_pred = [slope * x[i] + intercept for i in range(n)]
        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((y[i] - my) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        r = _correlation(x, y)

        return {
            "status": "success",
            "type": "simple_linear_regression",
            "equation": f"y = {round(slope, 4)}x + {round(intercept, 4)}",
            "slope": round(slope, 6),
            "intercept": round(intercept, 6),
            "r_squared": round(r_squared, 4),
            "correlation": round(r, 4),
            "n": n,
            "interpretation": f"X'teki 1 birimlik artis, Y'de {round(slope, 4)} birimlik {'artisa' if slope > 0 else 'azalmaya'} neden olur.",
            "model_quality": "iyi" if r_squared > 0.7 else ("orta" if r_squared > 0.4 else "zayif"),
        }


# ────────────────────────────────────────────────────────────────────────────
# 236 — time_series_analyzer
# ────────────────────────────────────────────────────────────────────────────
class TimeSeriesAnalyzer(BaseSkill):
    """Zaman serisi analizi."""

    SKILL_ID = "236"
    NAME = "time_series_analyzer"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "Zaman serisi analizi (trend, mevsimsellik, tahmin)"
    PARAMETERS = {
        "data": "Degerler dizisi",
        "date_column": "Tarih sutunu",
        "value_column": "Deger sutunu",
        "forecast_periods": "Tahmin periyodu",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        values = _to_float_list(params.get("data", []))
        forecast_n = int(params.get("forecast_periods", 3))

        if len(values) < 3:
            return {"status": "error", "message": "En az 3 veri noktasi gerekli"}

        n = len(values)

        # Trend (lineer)
        x = list(range(n))
        mx = _mean(x)
        my = _mean(values)
        ss_xy = sum((x[i] - mx) * (values[i] - my) for i in range(n))
        ss_xx = sum((xi - mx) ** 2 for xi in x)
        slope = ss_xy / ss_xx if ss_xx > 0 else 0
        intercept = my - slope * mx
        trend_direction = "yukselis" if slope > 0.01 else ("dususu" if slope < -0.01 else "yatay")

        # Hareketli ortalama (window=3)
        window = min(3, n)
        moving_avg = []
        for i in range(n - window + 1):
            moving_avg.append(round(_mean(values[i:i + window]), 4))

        # Basit tahmin (lineer trend)
        forecast = []
        for i in range(1, forecast_n + 1):
            pred = slope * (n + i) + intercept
            forecast.append(round(pred, 4))

        # Degisim oranlari
        changes = []
        for i in range(1, n):
            if values[i - 1] != 0:
                pct = (values[i] - values[i - 1]) / values[i - 1] * 100
                changes.append(round(pct, 2))

        return {
            "status": "success",
            "data_points": n,
            "trend": {
                "direction": trend_direction,
                "slope": round(slope, 4),
                "intercept": round(intercept, 4),
            },
            "statistics": {
                "mean": round(my, 4),
                "std": round(_std(values, 1), 4),
                "min": min(values),
                "max": max(values),
            },
            "moving_average": moving_avg,
            "period_changes_pct": changes,
            "forecast": forecast,
            "avg_change_pct": round(_mean(changes), 2) if changes else 0,
        }


# ────────────────────────────────────────────────────────────────────────────
# 237 — clustering_tool
# ────────────────────────────────────────────────────────────────────────────
class ClusteringTool(BaseSkill):
    """K-means kumeleme."""

    SKILL_ID = "237"
    NAME = "clustering_tool"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "K-means kumeleme"
    PARAMETERS = {
        "data": "Veri noktalari",
        "n_clusters": "Kume sayisi (varsayilan 3)",
        "features": "Ozellik isimleri",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        data = params.get("data", [])
        k = int(params.get("n_clusters", 3))

        if not data:
            return {"status": "error", "message": "Veri gerekli"}

        # 2D data: [[x1,y1], [x2,y2], ...]
        points: list[list[float]] = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, (list, tuple)):
                    points.append([float(x) for x in item])
                elif isinstance(item, dict):
                    points.append(list(float(v) for v in item.values() if isinstance(v, (int, float))))
                elif isinstance(item, (int, float)):
                    points.append([float(item)])

        if len(points) < k:
            return {"status": "error", "message": f"Veri noktasi ({len(points)}) kume sayisindan ({k}) az"}

        # Basit K-means
        dim = len(points[0])
        seed = int(hashlib.md5(str(data).encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        # Baslangic merkezleri
        centers = rng.sample(points, k)

        for _ in range(20):  # Max iterasyon
            # Atama
            clusters: dict[int, list[int]] = {i: [] for i in range(k)}
            for idx, point in enumerate(points):
                min_dist = float("inf")
                best_c = 0
                for c_idx, center in enumerate(centers):
                    dist = sum((point[d] - center[d]) ** 2 for d in range(dim))
                    if dist < min_dist:
                        min_dist = dist
                        best_c = c_idx
                clusters[best_c].append(idx)

            # Guncelle
            new_centers = []
            for c_idx in range(k):
                if clusters[c_idx]:
                    c_points = [points[i] for i in clusters[c_idx]]
                    new_center = [_mean([p[d] for p in c_points]) for d in range(dim)]
                    new_centers.append(new_center)
                else:
                    new_centers.append(centers[c_idx])

            if new_centers == centers:
                break
            centers = new_centers

        result_clusters = []
        for c_idx in range(k):
            members = clusters[c_idx]
            c_points = [points[i] for i in members]
            result_clusters.append({
                "cluster_id": c_idx,
                "center": [round(c, 4) for c in centers[c_idx]],
                "size": len(members),
                "members_preview": members[:10],
            })

        return {
            "status": "success",
            "n_clusters": k,
            "total_points": len(points),
            "dimensions": dim,
            "clusters": result_clusters,
        }


# ────────────────────────────────────────────────────────────────────────────
# 238 — text_analytics
# ────────────────────────────────────────────────────────────────────────────
class TextAnalytics(BaseSkill):
    """Metin analizi."""

    SKILL_ID = "238"
    NAME = "text_analytics"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "Metin analizi (kelime frekansi, n-gram, word cloud verisi)"
    PARAMETERS = {
        "text": "Metin",
        "operations": "Islemler (frequency/ngrams/readability/all)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        text = str(params.get("text", ""))
        operations = str(params.get("operations", "all")).lower()

        if not text:
            return {"status": "error", "message": "Metin gerekli"}

        words = text.lower().split()
        # Stop words (basit TR + EN)
        stop_words = {"bir", "ve", "ile", "de", "da", "bu", "su", "o", "ben", "sen",
                       "the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
                       "to", "for", "of", "and", "or", "but", "not", "it", "this", "that"}
        clean_words = [w.strip(".,!?;:()\"'") for w in words if w.strip(".,!?;:()\"'") not in stop_words and len(w) > 1]

        result: dict[str, Any] = {"status": "success"}

        if operations in ("frequency", "all"):
            freq = Counter(clean_words)
            result["word_frequency"] = [{"word": w, "count": c} for w, c in freq.most_common(20)]

        if operations in ("ngrams", "all"):
            # Bigrams
            bigrams = [f"{clean_words[i]} {clean_words[i + 1]}" for i in range(len(clean_words) - 1)]
            bg_freq = Counter(bigrams)
            result["bigrams"] = [{"bigram": b, "count": c} for b, c in bg_freq.most_common(10)]
            # Trigrams
            trigrams = [f"{clean_words[i]} {clean_words[i + 1]} {clean_words[i + 2]}" for i in range(len(clean_words) - 2)]
            tg_freq = Counter(trigrams)
            result["trigrams"] = [{"trigram": t, "count": c} for t, c in tg_freq.most_common(10)]

        if operations in ("readability", "all"):
            sentences = max(text.count(".") + text.count("!") + text.count("?"), 1)
            avg_word_len = _mean([len(w) for w in words]) if words else 0
            avg_sentence_len = len(words) / sentences
            result["readability"] = {
                "total_chars": len(text),
                "total_words": len(words),
                "total_sentences": sentences,
                "unique_words": len(set(clean_words)),
                "avg_word_length": round(avg_word_len, 2),
                "avg_sentence_length": round(avg_sentence_len, 2),
                "vocabulary_richness": round(len(set(clean_words)) / max(len(clean_words), 1), 3),
            }

        if operations == "all":
            result["summary"] = {
                "total_words": len(words),
                "unique_words": len(set(clean_words)),
                "most_common_word": Counter(clean_words).most_common(1)[0][0] if clean_words else None,
            }

        return result


# ────────────────────────────────────────────────────────────────────────────
# 239 — survey_analyzer
# ────────────────────────────────────────────────────────────────────────────
class SurveyAnalyzer(BaseSkill):
    """Anket sonuc analizi."""

    SKILL_ID = "239"
    NAME = "survey_analyzer"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "Anket sonuc analizi (frekans, capraz tablo, NPS)"
    PARAMETERS = {"data": "Anket verileri (dict dizisi)"}

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        data = params.get("data", [])

        if not data or not isinstance(data, list):
            # Demo veri
            data = [
                {"satisfaction": 9, "recommend": 10, "age_group": "25-34"},
                {"satisfaction": 7, "recommend": 8, "age_group": "35-44"},
                {"satisfaction": 3, "recommend": 2, "age_group": "25-34"},
                {"satisfaction": 8, "recommend": 9, "age_group": "45-54"},
                {"satisfaction": 6, "recommend": 5, "age_group": "35-44"},
                {"satisfaction": 9, "recommend": 10, "age_group": "25-34"},
                {"satisfaction": 4, "recommend": 3, "age_group": "45-54"},
                {"satisfaction": 8, "recommend": 8, "age_group": "35-44"},
            ]

        n = len(data)
        analysis: dict[str, Any] = {"total_responses": n}

        # Her alan icin frekans
        if data and isinstance(data[0], dict):
            for field in data[0].keys():
                values = [row.get(field) for row in data if row.get(field) is not None]
                if all(isinstance(v, (int, float)) for v in values):
                    nums = [float(v) for v in values]
                    analysis[field] = {
                        "type": "numeric",
                        "mean": round(_mean(nums), 2),
                        "median": round(_median(nums), 2),
                        "std": round(_std(nums, 1), 2),
                        "min": min(nums),
                        "max": max(nums),
                    }
                else:
                    freq = Counter(str(v) for v in values)
                    analysis[field] = {
                        "type": "categorical",
                        "distribution": dict(freq.most_common()),
                        "unique": len(freq),
                    }

        # NPS hesaplama (recommend alani varsa)
        recommend_values = [row.get("recommend") for row in data if isinstance(row.get("recommend"), (int, float))]
        if recommend_values:
            promoters = sum(1 for v in recommend_values if v >= 9)
            passives = sum(1 for v in recommend_values if 7 <= v <= 8)
            detractors = sum(1 for v in recommend_values if v <= 6)
            total = len(recommend_values)
            nps = round((promoters - detractors) / total * 100, 1)
            analysis["nps"] = {
                "score": nps,
                "promoters": promoters,
                "passives": passives,
                "detractors": detractors,
                "interpretation": "Mukemmel" if nps > 50 else ("Iyi" if nps > 0 else "Gelisim gerekli"),
            }

        return {"status": "success", "analysis": analysis}


# ────────────────────────────────────────────────────────────────────────────
# 240 — hypothesis_tester
# ────────────────────────────────────────────────────────────────────────────
class HypothesisTester(BaseSkill):
    """Istatistiksel hipotez testi."""

    SKILL_ID = "240"
    NAME = "hypothesis_tester"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "Istatistiksel hipotez testi (t-test, chi-square)"
    PARAMETERS = {
        "data": "Veri (iki grup icin ayri diziler)",
        "test_type": "Test tipi (t_test/z_test/proportion)",
        "alpha": "Anlamlilik duzeyi (varsayilan 0.05)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        data = params.get("data", {})
        test_type = str(params.get("test_type", "t_test")).lower()
        alpha = float(params.get("alpha", 0.05))

        if test_type in ("t_test", "z_test"):
            if isinstance(data, dict):
                group1 = _to_float_list(data.get("group1", data.get("a", [])))
                group2 = _to_float_list(data.get("group2", data.get("b", [])))
            elif isinstance(data, list) and len(data) >= 2:
                group1 = _to_float_list(data[0])
                group2 = _to_float_list(data[1])
            else:
                return {"status": "error", "message": "Iki grup verisi gerekli"}

            n1, n2 = len(group1), len(group2)
            if n1 < 2 or n2 < 2:
                return {"status": "error", "message": "Her grupta en az 2 veri noktasi gerekli"}

            m1, m2 = _mean(group1), _mean(group2)
            s1, s2 = _std(group1, 1), _std(group2, 1)

            # T-test (Welch's)
            se = math.sqrt(s1 ** 2 / n1 + s2 ** 2 / n2) if (s1 > 0 or s2 > 0) else 1
            t_stat = (m1 - m2) / se if se > 0 else 0

            # Yaklasik p-degeri (normal dagilim yakinsama)
            z = abs(t_stat)
            # Basit yaklasim
            if z > 3.5:
                p_value = 0.001
            elif z > 2.58:
                p_value = 0.01
            elif z > 1.96:
                p_value = 0.05
            elif z > 1.645:
                p_value = 0.10
            else:
                p_value = min(1.0, 2 * (1 - 0.5 * (1 + math.erf(z / math.sqrt(2)))))

            significant = p_value < alpha
            effect_size = abs(m1 - m2) / math.sqrt((s1 ** 2 + s2 ** 2) / 2) if (s1 > 0 or s2 > 0) else 0

            return {
                "status": "success",
                "test": "Welch's t-test",
                "group1": {"n": n1, "mean": round(m1, 4), "std": round(s1, 4)},
                "group2": {"n": n2, "mean": round(m2, 4), "std": round(s2, 4)},
                "t_statistic": round(t_stat, 4),
                "p_value": round(p_value, 4),
                "alpha": alpha,
                "significant": significant,
                "effect_size_cohen_d": round(effect_size, 4),
                "conclusion": f"Gruplar arasi fark istatistiksel olarak {'anlamli' if significant else 'anlamli degil'} (p={round(p_value, 4)}, α={alpha})",
            }

        if test_type == "proportion":
            successes1 = int(params.get("successes1", data.get("successes1", 50)))
            total1 = int(params.get("total1", data.get("total1", 100)))
            successes2 = int(params.get("successes2", data.get("successes2", 60)))
            total2 = int(params.get("total2", data.get("total2", 100)))

            p1 = successes1 / total1 if total1 else 0
            p2 = successes2 / total2 if total2 else 0
            p_pool = (successes1 + successes2) / (total1 + total2) if (total1 + total2) else 0
            se = math.sqrt(p_pool * (1 - p_pool) * (1 / total1 + 1 / total2)) if p_pool > 0 and p_pool < 1 else 1
            z = (p1 - p2) / se if se > 0 else 0

            p_value = min(1.0, 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2)))))

            return {
                "status": "success",
                "test": "z_test_proportions",
                "group1": {"proportion": round(p1, 4), "n": total1},
                "group2": {"proportion": round(p2, 4), "n": total2},
                "z_statistic": round(z, 4),
                "p_value": round(p_value, 4),
                "significant": p_value < alpha,
                "difference": round(p1 - p2, 4),
            }

        return {"status": "error", "message": f"Bilinmeyen test: {test_type}"}


# ────────────────────────────────────────────────────────────────────────────
# 241 — sample_size_calculator
# ────────────────────────────────────────────────────────────────────────────
class SampleSizeCalculator(BaseSkill):
    """Orneklem buyuklugu hesaplama."""

    SKILL_ID = "241"
    NAME = "sample_size_calculator"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "Orneklem buyuklugu hesaplama"
    PARAMETERS = {
        "confidence_level": "Guven duzeyi (0.90/0.95/0.99)",
        "margin_of_error": "Hata payi (0.01-0.10)",
        "population_size": "Populasyon buyuklugu (opsiyonel)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        conf = float(params.get("confidence_level", 0.95))
        moe = float(params.get("margin_of_error", 0.05))
        pop = params.get("population_size")

        z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z = z_scores.get(conf, 1.96)

        p = 0.5  # En kotu durum
        n_infinite = math.ceil((z ** 2 * p * (1 - p)) / (moe ** 2))

        if pop and int(pop) > 0:
            pop_n = int(pop)
            n_adjusted = math.ceil(n_infinite / (1 + (n_infinite - 1) / pop_n))
        else:
            pop_n = None
            n_adjusted = n_infinite

        return {
            "status": "success",
            "confidence_level": conf,
            "margin_of_error": moe,
            "z_score": z,
            "population_size": pop_n,
            "sample_size_infinite": n_infinite,
            "sample_size_adjusted": n_adjusted,
            "recommended_sample_size": n_adjusted,
            "note": "p=0.5 (en kotu durum) varsayilmistir. Gercek oran biliniyorsa daha kucuk orneklem yeterli olabilir.",
        }


# ────────────────────────────────────────────────────────────────────────────
# 242 — conversion_rate_analyzer
# ────────────────────────────────────────────────────────────────────────────
class ConversionRateAnalyzer(BaseSkill):
    """Donusum orani analizi."""

    SKILL_ID = "242"
    NAME = "conversion_rate_analyzer"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "Donusum orani analizi ve tahmin"
    PARAMETERS = {
        "visitors": "Ziyaretci sayisi",
        "conversions": "Donusum sayisi",
        "period": "Donem (daily/weekly/monthly)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        visitors = int(params.get("visitors", 1000))
        conversions = int(params.get("conversions", 30))
        period = str(params.get("period", "monthly")).lower()

        rate = conversions / visitors if visitors > 0 else 0

        # Guven araligi (Wilson)
        z = 1.96
        n = visitors
        p_hat = rate
        denom = 1 + z ** 2 / n
        center = (p_hat + z ** 2 / (2 * n)) / denom
        spread = z * math.sqrt((p_hat * (1 - p_hat) + z ** 2 / (4 * n)) / n) / denom

        ci_lower = max(0, center - spread)
        ci_upper = min(1, center + spread)

        # Karsilastirma
        benchmarks = {
            "e_ticaret": 0.02,
            "saas": 0.03,
            "landing_page": 0.05,
            "email": 0.025,
        }

        return {
            "status": "success",
            "visitors": visitors,
            "conversions": conversions,
            "conversion_rate": round(rate * 100, 2),
            "confidence_interval_95": {
                "lower": round(ci_lower * 100, 2),
                "upper": round(ci_upper * 100, 2),
            },
            "period": period,
            "benchmarks": {k: f"{v * 100:.1f}%" for k, v in benchmarks.items()},
            "vs_benchmark": {k: "uzerinde" if rate > v else "altinda" for k, v in benchmarks.items()},
            "improvement_potential": round((0.05 - rate) / max(rate, 0.001) * 100, 1) if rate < 0.05 else 0,
        }


# ────────────────────────────────────────────────────────────────────────────
# 243 — cohort_analyzer
# ────────────────────────────────────────────────────────────────────────────
class CohortAnalyzer(BaseSkill):
    """Kohort analizi."""

    SKILL_ID = "243"
    NAME = "cohort_analyzer"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "Kohort analizi (retention, churn)"
    PARAMETERS = {
        "data": "Kohort verileri",
        "cohort_column": "Kohort sutunu",
        "date_column": "Tarih sutunu",
        "metric": "Metrik (retention/churn/revenue)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        metric = str(params.get("metric", "retention")).lower()

        # Demo kohort verisi
        cohorts = {
            "Ocak": {"month_0": 100, "month_1": 60, "month_2": 45, "month_3": 35, "month_4": 30},
            "Subat": {"month_0": 120, "month_1": 72, "month_2": 50, "month_3": 40},
            "Mart": {"month_0": 90, "month_1": 50, "month_2": 38},
            "Nisan": {"month_0": 110, "month_1": 65},
        }

        data = params.get("data")
        if isinstance(data, dict) and data:
            cohorts = data

        retention_table: dict[str, dict[str, float]] = {}
        for cohort, values in cohorts.items():
            base = values.get("month_0", list(values.values())[0] if values else 100)
            retention_table[cohort] = {}
            for period, count in values.items():
                if metric == "retention":
                    retention_table[cohort][period] = round(count / base * 100, 1)
                elif metric == "churn":
                    retention_table[cohort][period] = round((1 - count / base) * 100, 1)
                else:
                    retention_table[cohort][period] = count

        # Ortalama retention
        all_periods: dict[str, list[float]] = {}
        for cohort_data in retention_table.values():
            for period, val in cohort_data.items():
                if period not in all_periods:
                    all_periods[period] = []
                all_periods[period].append(val)

        avg_by_period = {p: round(_mean(vals), 1) for p, vals in all_periods.items()}

        return {
            "status": "success",
            "metric": metric,
            "cohort_count": len(cohorts),
            "cohort_table": retention_table,
            "average_by_period": avg_by_period,
            "insight": "Ilk ayda en buyuk kayip yasaniyor. Onboarding surecini iyilestirmeye odaklanin.",
        }


# ────────────────────────────────────────────────────────────────────────────
# 244 — funnel_analyzer
# ────────────────────────────────────────────────────────────────────────────
class FunnelAnalyzer(BaseSkill):
    """Donusum hunisi analizi."""

    SKILL_ID = "244"
    NAME = "funnel_analyzer"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "Donusum hunisi analizi (drop-off noktalari)"
    PARAMETERS = {"stages": "Huni asamalari (isim:sayi seklinde veya dict dizisi)"}

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        stages_raw = params.get("stages", [])

        stages: list[dict[str, Any]] = []
        if isinstance(stages_raw, list):
            for item in stages_raw:
                if isinstance(item, dict):
                    stages.append(item)
                elif isinstance(item, str) and ":" in item:
                    name, count = item.split(":", 1)
                    stages.append({"name": name.strip(), "count": int(count.strip())})

        if not stages:
            stages = [
                {"name": "Ziyaret", "count": 10000},
                {"name": "Urun Goruntuleme", "count": 5000},
                {"name": "Sepete Ekle", "count": 1500},
                {"name": "Odeme Baslat", "count": 800},
                {"name": "Satin Alma", "count": 400},
            ]

        first_count = stages[0]["count"]
        analysis: list[dict[str, Any]] = []

        for i, stage in enumerate(stages):
            entry: dict[str, Any] = {
                "stage": stage["name"],
                "count": stage["count"],
                "conversion_from_top": round(stage["count"] / first_count * 100, 2),
            }
            if i > 0:
                prev = stages[i - 1]["count"]
                entry["conversion_from_prev"] = round(stage["count"] / prev * 100, 2) if prev else 0
                entry["drop_off_count"] = prev - stage["count"]
                entry["drop_off_pct"] = round((prev - stage["count"]) / prev * 100, 2) if prev else 0
            else:
                entry["conversion_from_prev"] = 100.0
                entry["drop_off_count"] = 0
                entry["drop_off_pct"] = 0.0

            analysis.append(entry)

        # En buyuk drop-off
        worst_drop = max(analysis[1:], key=lambda x: x["drop_off_pct"]) if len(analysis) > 1 else None

        return {
            "status": "success",
            "total_stages": len(stages),
            "overall_conversion": round(stages[-1]["count"] / first_count * 100, 2) if stages else 0,
            "funnel_analysis": analysis,
            "biggest_drop_off": {
                "stage": worst_drop["stage"],
                "drop_off_pct": worst_drop["drop_off_pct"],
                "recommendation": f"'{worst_drop['stage']}' asamasinda %{worst_drop['drop_off_pct']} kayip var. Bu noktayi iyilestirin.",
            } if worst_drop else None,
        }


# ────────────────────────────────────────────────────────────────────────────
# 245 — customer_segmenter
# ────────────────────────────────────────────────────────────────────────────
class CustomerSegmenter(BaseSkill):
    """RFM veya davranis bazli musteri segmentasyonu."""

    SKILL_ID = "245"
    NAME = "customer_segmenter"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "RFM veya davranis bazli musteri segmentasyonu"
    PARAMETERS = {
        "data": "Musteri verileri",
        "method": "Yontem (rfm/behavioral)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        method = str(params.get("method", "rfm")).lower()

        if method == "rfm":
            # Demo RFM
            customers = params.get("data", [
                {"id": "C001", "recency_days": 5, "frequency": 12, "monetary": 5000},
                {"id": "C002", "recency_days": 90, "frequency": 2, "monetary": 500},
                {"id": "C003", "recency_days": 15, "frequency": 8, "monetary": 3000},
                {"id": "C004", "recency_days": 200, "frequency": 1, "monetary": 100},
                {"id": "C005", "recency_days": 10, "frequency": 15, "monetary": 8000},
            ])

            segments: dict[str, list[str]] = {
                "sampiyon": [], "sadik": [], "potansiyel": [],
                "risk_altinda": [], "kayip": [],
            }

            for c in customers:
                r = c.get("recency_days", 30)
                f = c.get("frequency", 1)
                m = c.get("monetary", 0)
                cid = c.get("id", "?")

                if r <= 15 and f >= 10 and m >= 3000:
                    segments["sampiyon"].append(cid)
                elif r <= 30 and f >= 5:
                    segments["sadik"].append(cid)
                elif r <= 60 and f >= 2:
                    segments["potansiyel"].append(cid)
                elif r <= 120:
                    segments["risk_altinda"].append(cid)
                else:
                    segments["kayip"].append(cid)

            return {
                "status": "success",
                "method": "RFM",
                "total_customers": len(customers),
                "segments": {k: {"count": len(v), "customers": v} for k, v in segments.items()},
                "actions": {
                    "sampiyon": "Ozel odullerle motive edin",
                    "sadik": "Sadakat programina davet edin",
                    "potansiyel": "Upsell firsatlari sunun",
                    "risk_altinda": "Geri kazanim kampanyasi baslatin",
                    "kayip": "Ozel indirim teklifi gonderin",
                },
            }

        return {"status": "success", "method": method, "note": "Sadece RFM yontemi destekleniyor"}


# ────────────────────────────────────────────────────────────────────────────
# 246 — churn_predictor
# ────────────────────────────────────────────────────────────────────────────
class ChurnPredictor(BaseSkill):
    """Musteri kayip tahmini."""

    SKILL_ID = "246"
    NAME = "churn_predictor"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "Musteri kayip tahmini"
    PARAMETERS = {"customer_data": "Musteri verileri"}

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        data = params.get("customer_data", [])

        if not data:
            data = [
                {"id": "C001", "last_purchase_days": 5, "frequency": 12, "complaints": 0, "support_tickets": 1},
                {"id": "C002", "last_purchase_days": 90, "frequency": 2, "complaints": 3, "support_tickets": 5},
                {"id": "C003", "last_purchase_days": 180, "frequency": 1, "complaints": 2, "support_tickets": 8},
                {"id": "C004", "last_purchase_days": 10, "frequency": 8, "complaints": 0, "support_tickets": 0},
            ]

        predictions: list[dict[str, Any]] = []
        for c in data:
            cid = c.get("id", "?")
            recency = c.get("last_purchase_days", 30)
            freq = c.get("frequency", 1)
            complaints = c.get("complaints", 0)
            tickets = c.get("support_tickets", 0)

            # Basit skor modeli
            risk_score = 0
            risk_score += min(40, recency / 5)  # Recency: 0-40
            risk_score += max(0, 20 - freq * 2)  # Frequency: 0-20
            risk_score += min(20, complaints * 10)  # Complaints: 0-20
            risk_score += min(20, tickets * 4)  # Tickets: 0-20
            risk_score = min(100, risk_score)

            risk_label = "yuksek" if risk_score > 60 else ("orta" if risk_score > 30 else "dusuk")

            predictions.append({
                "customer_id": cid,
                "churn_risk_score": round(risk_score, 1),
                "risk_level": risk_label,
                "factors": {
                    "recency_impact": "yuksek" if recency > 60 else "dusuk",
                    "frequency_impact": "yuksek" if freq < 3 else "dusuk",
                    "complaint_impact": "yuksek" if complaints > 1 else "dusuk",
                },
            })

        predictions.sort(key=lambda x: x["churn_risk_score"], reverse=True)
        high_risk = [p for p in predictions if p["risk_level"] == "yuksek"]

        return {
            "status": "success",
            "total_customers": len(predictions),
            "high_risk_count": len(high_risk),
            "predictions": predictions,
            "recommendation": f"{len(high_risk)} musteri yuksek kayip riskinde. Oncelikle iletisime gecin.",
        }


# ────────────────────────────────────────────────────────────────────────────
# 247 — ltv_calculator
# ────────────────────────────────────────────────────────────────────────────
class LtvCalculator(BaseSkill):
    """Musteri yasam boyu degeri hesaplama."""

    SKILL_ID = "247"
    NAME = "ltv_calculator"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "Musteri yasam boyu degeri (LTV) hesaplama"
    PARAMETERS = {
        "avg_revenue": "Ortalama aylik gelir (musteri basina)",
        "churn_rate": "Aylik kayip orani (0-1)",
        "margin": "Kar marji (0-1)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        avg_rev = float(params.get("avg_revenue", 100))
        churn = float(params.get("churn_rate", 0.05))
        margin = float(params.get("margin", 0.3))

        if churn <= 0:
            return {"status": "error", "message": "Kayip orani sifirdan buyuk olmali"}

        avg_lifespan_months = 1 / churn
        ltv_revenue = avg_rev * avg_lifespan_months
        ltv_profit = ltv_revenue * margin

        return {
            "status": "success",
            "avg_monthly_revenue": avg_rev,
            "monthly_churn_rate": churn,
            "profit_margin": margin,
            "avg_customer_lifespan_months": round(avg_lifespan_months, 1),
            "avg_customer_lifespan_years": round(avg_lifespan_months / 12, 1),
            "ltv_revenue": round(ltv_revenue, 2),
            "ltv_profit": round(ltv_profit, 2),
            "monthly_profit_per_customer": round(avg_rev * margin, 2),
            "formula": "LTV = Ortalama Gelir / Kayip Orani * Marj",
        }


# ────────────────────────────────────────────────────────────────────────────
# 248 — market_size_estimator
# ────────────────────────────────────────────────────────────────────────────
class MarketSizeEstimator(BaseSkill):
    """Pazar buyuklugu tahmini (TAM/SAM/SOM)."""

    SKILL_ID = "248"
    NAME = "market_size_estimator"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "Pazar buyuklugu tahmini (TAM/SAM/SOM)"
    PARAMETERS = {
        "industry": "Sektor",
        "geography": "Cografi bolge",
        "segment": "Hedef segment",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        industry = str(params.get("industry", "e-ticaret"))
        geography = str(params.get("geography", "Turkiye"))
        segment = str(params.get("segment", ""))

        # Deterministik tahmini degerler
        seed = int(hashlib.md5(f"{industry}{geography}".encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        tam = rng.randint(5, 50) * 1_000_000_000  # $5B - $50B
        sam_pct = rng.uniform(0.10, 0.30)
        som_pct = rng.uniform(0.01, 0.05)

        sam = int(tam * sam_pct)
        som = int(tam * som_pct)
        growth_rate = round(rng.uniform(5, 25), 1)

        return {
            "status": "success",
            "industry": industry,
            "geography": geography,
            "segment": segment,
            "tam": {"value": tam, "label": "Total Addressable Market",
                    "formatted": f"${tam / 1e9:.1f}B"},
            "sam": {"value": sam, "label": "Serviceable Addressable Market",
                    "formatted": f"${sam / 1e9:.1f}B", "pct_of_tam": f"{sam_pct * 100:.1f}%"},
            "som": {"value": som, "label": "Serviceable Obtainable Market",
                    "formatted": f"${som / 1e6:.0f}M", "pct_of_tam": f"{som_pct * 100:.2f}%"},
            "annual_growth_rate": f"{growth_rate}%",
            "5_year_projection": f"${som * (1 + growth_rate / 100) ** 5 / 1e6:.0f}M",
            "note": "Tahminler ornek verilerle uretilmistir. Gercek pazar arastirmasi onerilir.",
        }


# ────────────────────────────────────────────────────────────────────────────
# 249 — pricing_optimizer
# ────────────────────────────────────────────────────────────────────────────
class PricingOptimizer(BaseSkill):
    """Fiyatlandirma stratejisi analizi."""

    SKILL_ID = "249"
    NAME = "pricing_optimizer"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "Fiyatlandirma stratejisi analizi"
    PARAMETERS = {
        "cost": "Birim maliyet",
        "competitors_prices": "Rakip fiyatlari (dizi)",
        "demand_elasticity": "Talep esnekligi (varsayilan -1.5)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        cost = float(params.get("cost", 50))
        competitors = params.get("competitors_prices", [])
        elasticity = float(params.get("demand_elasticity", -1.5))

        if isinstance(competitors, str):
            competitors = [float(x.strip()) for x in competitors.split(",") if x.strip()]
        competitors = [float(x) for x in competitors] if competitors else [cost * 2, cost * 2.5, cost * 3]

        avg_competitor = _mean(competitors)
        min_competitor = min(competitors)
        max_competitor = max(competitors)

        strategies = {
            "maliyet_arti": {
                "price": round(cost * 1.5, 2),
                "margin": "50%",
                "description": "Maliyet + %50 kar marji",
            },
            "rekabetci": {
                "price": round(avg_competitor * 0.95, 2),
                "margin": f"{round((avg_competitor * 0.95 - cost) / cost * 100, 1)}%",
                "description": "Ortalama rakip fiyatinin %5 altinda",
            },
            "premium": {
                "price": round(max_competitor * 1.1, 2),
                "margin": f"{round((max_competitor * 1.1 - cost) / cost * 100, 1)}%",
                "description": "En yuksek rakipten %10 fazla",
            },
            "penetrasyon": {
                "price": round(min_competitor * 0.8, 2),
                "margin": f"{round((min_competitor * 0.8 - cost) / cost * 100, 1)}%",
                "description": "En dusuk rakipten %20 daha ucuz",
            },
        }

        # Optimal fiyat (basit esneklik modeli)
        if elasticity != 0:
            optimal = round(cost * abs(elasticity) / (abs(elasticity) - 1), 2) if abs(elasticity) > 1 else cost * 2
        else:
            optimal = cost * 2

        return {
            "status": "success",
            "unit_cost": cost,
            "competitor_prices": competitors,
            "competitor_avg": round(avg_competitor, 2),
            "demand_elasticity": elasticity,
            "optimal_price": optimal,
            "strategies": strategies,
            "recommendation": f"Esneklik {elasticity} ise optimal fiyat {optimal} TL. Rakip ortalamasi {round(avg_competitor, 2)} TL.",
        }


# ────────────────────────────────────────────────────────────────────────────
# 250 — unit_economics
# ────────────────────────────────────────────────────────────────────────────
class UnitEconomics(BaseSkill):
    """Birim ekonomi hesaplama."""

    SKILL_ID = "250"
    NAME = "unit_economics"
    CATEGORY = "data_science"
    RISK_LEVEL = "low"
    DESCRIPTION = "Birim ekonomi hesaplama (CAC, LTV, payback period, LTV/CAC)"
    PARAMETERS = {
        "cac": "Musteri edinme maliyeti",
        "ltv": "Musteri yasam boyu degeri",
        "monthly_revenue": "Aylik musteri geliri",
        "monthly_cost": "Aylik musteri maliyeti",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        cac = float(params.get("cac", 100))
        ltv = float(params.get("ltv", 500))
        monthly_rev = float(params.get("monthly_revenue", 50))
        monthly_cost = float(params.get("monthly_cost", 20))

        monthly_profit = monthly_rev - monthly_cost
        ltv_cac_ratio = ltv / cac if cac > 0 else float("inf")
        payback_months = cac / monthly_profit if monthly_profit > 0 else float("inf")
        margin = (monthly_rev - monthly_cost) / monthly_rev * 100 if monthly_rev > 0 else 0

        # Saglik degerlendirmesi
        if ltv_cac_ratio >= 3:
            health = "saglikli"
            note = "LTV/CAC >= 3: Buyume icin yatirim yapin"
        elif ltv_cac_ratio >= 1:
            health = "riskli"
            note = "LTV/CAC 1-3: CAC'yi dusurmeye veya LTV'yi artirmaya odaklanin"
        else:
            health = "surdurulemez"
            note = "LTV/CAC < 1: Acil maliyet optimizasyonu gerekli"

        return {
            "status": "success",
            "cac": cac,
            "ltv": ltv,
            "ltv_cac_ratio": round(ltv_cac_ratio, 2),
            "payback_period_months": round(payback_months, 1) if payback_months != float("inf") else "N/A",
            "monthly_revenue": monthly_rev,
            "monthly_cost": monthly_cost,
            "monthly_profit": round(monthly_profit, 2),
            "gross_margin_pct": round(margin, 1),
            "annual_revenue_per_customer": round(monthly_rev * 12, 2),
            "annual_profit_per_customer": round(monthly_profit * 12, 2),
            "health": health,
            "recommendation": note,
            "benchmarks": {
                "ideal_ltv_cac": ">= 3.0",
                "ideal_payback": "<= 12 ay",
                "your_ltv_cac": round(ltv_cac_ratio, 2),
                "your_payback": f"{round(payback_months, 1)} ay" if payback_months != float("inf") else "N/A",
            },
        }


# ────────────────────────────────────────────────────────────────────────────
# Modul disa aktarma
# ────────────────────────────────────────────────────────────────────────────

ALL_DATA_SCIENCE_SKILLS: list[type[BaseSkill]] = [
    StatisticsCalculator,     # 226
    ProbabilityCalculator,    # 227
    MatrixCalculator,         # 228
    EquationSolver,           # 229
    GraphPlotter,             # 230
    DataCleaner,              # 231
    DataProfiler,             # 232
    PivotTable,               # 233
    CorrelationFinder,        # 234
    RegressionAnalyzer,       # 235
    TimeSeriesAnalyzer,       # 236
    ClusteringTool,           # 237
    TextAnalytics,            # 238
    SurveyAnalyzer,           # 239
    HypothesisTester,         # 240
    SampleSizeCalculator,     # 241
    ConversionRateAnalyzer,   # 242
    CohortAnalyzer,           # 243
    FunnelAnalyzer,           # 244
    CustomerSegmenter,        # 245
    ChurnPredictor,           # 246
    LtvCalculator,            # 247
    MarketSizeEstimator,      # 248
    PricingOptimizer,         # 249
    UnitEconomics,            # 250
]
