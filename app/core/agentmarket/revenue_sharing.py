"""ATLAS Revenue Sharing modulu.

Gelir paylasimi: islem kaydi, yazar kazanci,
platform geliri, odeme isleme.
"""

import logging
import time
from typing import Any
from uuid import uuid4

from app.models.agentmarket_models import (
    RevenueRecord,
)

logger = logging.getLogger(__name__)

_DEFAULT_PLATFORM_FEE_PCT = 30.0
_MIN_PAYOUT_AMOUNT = 10.0
_DEFAULT_CURRENCY = "USD"


class RevenueSharing:
    """Gelir paylasim sistemi.

    Yazar ve platform arasindaki gelir
    paylasimini yonetir.

    Attributes:
        _records: Gelir kayitlari.
        _configs: Listeleme gelir yapilandirmalari.
        _pending_payouts: Bekleyen odemeler.
        _stats: Istatistikler.
    """

    def __init__(
        self,
        default_fee_pct: float = _DEFAULT_PLATFORM_FEE_PCT,
    ) -> None:
        """Gelir paylasimini baslatir.

        Args:
            default_fee_pct: Varsayilan platform komisyonu.
        """
        self._records: dict[
            str, RevenueRecord
        ] = {}
        self._configs: dict[
            str, dict[str, Any]
        ] = {}
        self._pending_payouts: dict[
            str, float
        ] = {}
        self._processed_payouts: list[
            dict[str, Any]
        ] = []
        self._default_fee_pct = default_fee_pct
        self._stats = {
            "transactions": 0,
            "total_gross": 0.0,
            "total_platform_fee": 0.0,
            "total_author_earnings": 0.0,
            "payouts_processed": 0,
        }

        logger.info(
            "RevenueSharing baslatildi, "
            "varsayilan komisyon: %.1f%%",
            default_fee_pct,
        )

    def configure(
        self,
        listing_id: str,
        author_id: str,
        platform_fee_pct: float | None = None,
    ) -> dict[str, Any]:
        """Listeleme gelir yapilandirmasi.

        Args:
            listing_id: Listeleme ID.
            author_id: Yazar ID.
            platform_fee_pct: Platform komisyonu.

        Returns:
            Yapilandirma bilgisi.
        """
        fee_pct = (
            platform_fee_pct
            if platform_fee_pct is not None
            else self._default_fee_pct
        )

        config = {
            "listing_id": listing_id,
            "author_id": author_id,
            "platform_fee_pct": fee_pct,
            "configured_at": time.time(),
        }
        self._configs[listing_id] = config

        logger.info(
            "Gelir yapilandirmasi: %s, "
            "yazar: %s, komisyon: %.1f%%",
            listing_id, author_id, fee_pct,
        )
        return config

    def record_transaction(
        self,
        listing_id: str,
        amount: float,
        currency: str = _DEFAULT_CURRENCY,
    ) -> RevenueRecord:
        """Islem kaydeder.

        Args:
            listing_id: Listeleme ID.
            amount: Brut tutar.
            currency: Para birimi.

        Returns:
            Gelir kaydi.
        """
        config = self._configs.get(
            listing_id, {},
        )
        author_id = config.get(
            "author_id", "unknown",
        )
        fee_pct = config.get(
            "platform_fee_pct",
            self._default_fee_pct,
        )

        platform_fee = amount * fee_pct / 100
        net_amount = amount - platform_fee

        # Mevcut donem kaydini guncelle veya
        # yeni kayit olustur
        period = time.strftime("%Y-%m")

        record = RevenueRecord(
            listing_id=listing_id,
            author_id=author_id,
            period=period,
            gross_amount=amount,
            platform_fee_pct=fee_pct,
            net_amount=net_amount,
            currency=currency,
            transactions_count=1,
        )

        self._records[record.id] = record

        # Bekleyen odemeleri guncelle
        current = self._pending_payouts.get(
            author_id, 0.0,
        )
        self._pending_payouts[author_id] = (
            current + net_amount
        )

        # Istatistikleri guncelle
        self._stats["transactions"] += 1
        self._stats["total_gross"] += amount
        self._stats[
            "total_platform_fee"
        ] += platform_fee
        self._stats[
            "total_author_earnings"
        ] += net_amount

        logger.info(
            "Islem kaydedildi: %s, brut: %.2f, "
            "net: %.2f %s",
            listing_id, amount,
            net_amount, currency,
        )
        return record

    def get_author_earnings(
        self,
        author_id: str,
        period: str | None = None,
    ) -> dict[str, Any]:
        """Yazar kazancini hesaplar.

        Args:
            author_id: Yazar ID.
            period: Donem filtresi (YYYY-MM).

        Returns:
            Kazanc bilgisi.
        """
        records = [
            r for r in self._records.values()
            if r.author_id == author_id
            and (
                not period
                or r.period == period
            )
        ]

        total_gross = sum(
            r.gross_amount for r in records
        )
        total_net = sum(
            r.net_amount for r in records
        )
        total_fee = total_gross - total_net
        tx_count = sum(
            r.transactions_count
            for r in records
        )

        return {
            "author_id": author_id,
            "period": period or "all",
            "total_gross": round(
                total_gross, 2,
            ),
            "total_net": round(total_net, 2),
            "total_fees": round(total_fee, 2),
            "transactions": tx_count,
            "records": len(records),
            "pending_payout": round(
                self._pending_payouts.get(
                    author_id, 0.0,
                ),
                2,
            ),
        }

    def get_listing_revenue(
        self,
        listing_id: str,
    ) -> dict[str, Any]:
        """Listeleme gelirini hesaplar.

        Args:
            listing_id: Listeleme ID.

        Returns:
            Gelir bilgisi.
        """
        records = [
            r for r in self._records.values()
            if r.listing_id == listing_id
        ]

        total_gross = sum(
            r.gross_amount for r in records
        )
        total_net = sum(
            r.net_amount for r in records
        )
        tx_count = sum(
            r.transactions_count
            for r in records
        )

        return {
            "listing_id": listing_id,
            "total_gross": round(
                total_gross, 2,
            ),
            "total_net": round(total_net, 2),
            "total_fees": round(
                total_gross - total_net, 2,
            ),
            "transactions": tx_count,
            "records": len(records),
        }

    def get_platform_revenue(
        self,
        period: str | None = None,
    ) -> dict[str, Any]:
        """Platform gelirini hesaplar.

        Args:
            period: Donem filtresi (YYYY-MM).

        Returns:
            Platform gelir bilgisi.
        """
        records = [
            r for r in self._records.values()
            if (
                not period
                or r.period == period
            )
        ]

        total_gross = sum(
            r.gross_amount for r in records
        )
        total_fees = sum(
            r.gross_amount - r.net_amount
            for r in records
        )
        total_payouts = sum(
            r.net_amount for r in records
        )

        return {
            "period": period or "all",
            "total_gross": round(
                total_gross, 2,
            ),
            "platform_fees": round(
                total_fees, 2,
            ),
            "author_payouts": round(
                total_payouts, 2,
            ),
            "transactions": len(records),
        }

    def process_payout(
        self,
        author_id: str,
    ) -> dict[str, Any]:
        """Odeme isler.

        Args:
            author_id: Yazar ID.

        Returns:
            Odeme bilgisi.
        """
        pending = self._pending_payouts.get(
            author_id, 0.0,
        )

        if pending < _MIN_PAYOUT_AMOUNT:
            return {
                "author_id": author_id,
                "status": "below_minimum",
                "pending": round(pending, 2),
                "minimum": _MIN_PAYOUT_AMOUNT,
            }

        payout = {
            "payout_id": str(uuid4())[:8],
            "author_id": author_id,
            "amount": round(pending, 2),
            "currency": _DEFAULT_CURRENCY,
            "status": "processed",
            "processed_at": time.time(),
        }

        self._pending_payouts[author_id] = 0.0
        self._processed_payouts.append(payout)
        self._stats["payouts_processed"] += 1

        logger.info(
            "Odeme islendi: %s, tutar: %.2f",
            author_id, pending,
        )
        return payout

    def get_pending_payouts(
        self,
    ) -> list[dict[str, Any]]:
        """Bekleyen odemeleri listeler.

        Returns:
            Bekleyen odeme listesi.
        """
        return [
            {
                "author_id": author_id,
                "pending_amount": round(
                    amount, 2,
                ),
                "currency": _DEFAULT_CURRENCY,
                "eligible": (
                    amount >= _MIN_PAYOUT_AMOUNT
                ),
            }
            for author_id, amount
            in self._pending_payouts.items()
            if amount > 0
        ]

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik bilgileri.
        """
        return {
            "total_records": len(self._records),
            "configured_listings": len(
                self._configs,
            ),
            "pending_payouts_count": sum(
                1 for a in (
                    self._pending_payouts.values()
                )
                if a > 0
            ),
            "total_pending_amount": round(
                sum(
                    self._pending_payouts.values()
                ),
                2,
            ),
            **{
                k: (
                    round(v, 2)
                    if isinstance(v, float)
                    else v
                )
                for k, v in self._stats.items()
            },
        }
