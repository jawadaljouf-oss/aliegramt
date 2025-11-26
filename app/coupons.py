import json
import random
from typing import Optional, Dict, Any, List, Tuple
from .config import COUPONS_FILE


class CouponManager:
    def __init__(self, coupons_path=COUPONS_FILE):
        self.coupons_path = coupons_path
        self._ranges: List[Dict[str, Any]] = []
        self.load_coupons()

    def load_coupons(self) -> None:
        """تحميل شرائح الأسعار والكوبونات من ملف JSON."""
        if not self.coupons_path.exists():
            raise FileNotFoundError(f"Coupons file not found: {self.coupons_path}")

        with open(self.coupons_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._ranges = data.get("ranges", [])

    def find_range(self, price: float) -> Optional[Dict[str, Any]]:
        """إيجاد الشريحة التي يقع فيها السعر."""
        for r in self._ranges:
            min_price = r.get("min_price")
            max_price = r.get("max_price")
            if min_price is None or max_price is None:
                continue
            if min_price <= price <= max_price:
                return r
        return None

    def get_random_coupon_for_price(
        self, price: float
    ) -> Tuple[Optional[Dict[str, Any]], Optional[float]]:
        """
        إرجاع كوبون عشوائي يناسب هذا السعر، مع السعر بعد الخصم.
        إذا لم توجد شريحة مناسبة أو لا توجد كوبونات، يرجع (None, None).
        """
        price = float(price)
        price_range = self.find_range(price)
        if not price_range:
            return None, None

        coupons = price_range.get("coupons", [])
        if not coupons:
            return None, None

        coupon = random.choice(coupons)
        discount = float(coupon.get("discount", 0))
        final_price = max(price - discount, 0.0)
        return coupon, final_price


# مثال استخدام (للاختبار المحلي فقط)
if __name__ == "__main__":
    manager = CouponManager()
    test_price = 27.5
    coupon, final_price = manager.get_random_coupon_for_price(test_price)
    print("Price:", test_price)
    print("Coupon:", coupon)
    print("Final price:", final_price)
