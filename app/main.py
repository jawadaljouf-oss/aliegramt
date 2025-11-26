from flask import Flask, jsonify
from .config import POST_PREFIX_TEXT
from .coupons import CouponManager
from .telegram_bot import TelegramBot
from .product_selector import ProductSelector
# من بعد سنضيف: from .aliexpress_api import AliExpressApiClient


def create_app():
    app = Flask(__name__)

    # تهيئة المكوّنات المشتركة
    coupon_manager = CouponManager()
    telegram_bot = TelegramBot()

    # Placeholder مؤقت لـ ali_client إلى أن نكمل ملف aliexpress_api.py
    class DummyAliClient:
        def search_products(self, category_info, limit):
            # هذا للاختبار فقط؛ لاحقاً سنستبدله بالاتصال الحقيقي مع API
            return []

    ali_client = DummyAliClient()
    product_selector = ProductSelector(ali_client)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200

    @app.route("/publish", methods=["GET"])
    def publish():
        # 1) اختيار منتج
        product = product_selector.get_random_product()
        if not product:
            return jsonify({"status": "error", "message": "No products found"}), 500

        # نتوقع أن المنتج يحتوي على الحقول التالية من API:
        # id, title, original_price, image_url, affiliate_url
        title = product.get("title")
        original_price = float(product.get("original_price", 0))
        image_url = product.get("image_url")
        affiliate_url = product.get("affiliate_url")

        # 2) اختيار كوبون عشوائي مناسب لهذا السعر
        coupon, final_price = coupon_manager.get_random_coupon_for_price(original_price)

        # في حال لا يوجد كوبون مناسب
        if coupon is None or final_price is None:
            coupon_text = "لا يوجد كوبون مناسب لهذا السعر حالياً"
            final_price_text = f"{original_price:.2f} دولار"
        else:
            code = coupon.get("code")
            discount = coupon.get("discount")
            coupon_text = f"الكوبون المستخدم: {code} (خصم {discount} دولار)"
            final_price_text = f"{final_price:.2f} دولار"

        # 3) بناء نص الرسالة
        lines = [
            f"{POST_PREFIX_TEXT}: {title}",
            f"السعر الأصلي: {original_price:.2f} دولار",
            coupon_text,
            f"السعر بعد الخصم: {final_price_text}",
            "",
            f"رابط المنتج: {affiliate_url}",
        ]
        message_text = "\n".join(lines)

        # 4) إرسال إلى تيليجرام
        if image_url:
            telegram_bot.send_photo_with_caption(
                photo_url=image_url,
                caption=message_text,
            )
        else:
            telegram_bot.send_text(text=message_text)

        return jsonify({"status": "ok"}), 200

    return app


# لتشغيل محلياً: FLASK_APP=app.main flask run
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
