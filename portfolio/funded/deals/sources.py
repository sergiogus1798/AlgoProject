"""Where each firm shows its offers: Hantec's banner and code check, FTMO's pricing table, FundedNext's catalogue."""

import html
import http.cookiejar
import json
import re
import urllib.request

from portfolio.funded.catalog import ftmo, fundednext, hantec

PAGE = "https://myhtrader.hmarkets.com/purchasechallenge"
UA = {"User-Agent": "Mozilla/5.0"}


def _hantec_session() -> tuple[urllib.request.OpenerDirector, str, str]:
    """A cookie session on the purchase page, the page, and its anti-forgery token."""
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    page = opener.open(urllib.request.Request(PAGE, headers=UA), timeout=60).read().decode()
    token = re.search(r'__RequestVerificationToken[^>]*value="([^"]+)"', page).group(1)
    return opener, page, token


def hantec_banners() -> list[dict]:
    """Every "NN% off …" line the purchase page prints. A banner carries no code: the code is found elsewhere."""
    _, page, _ = _hantec_session()
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", page)))
    found = {m.group(0).strip() for m in re.finditer(r"\d{1,2}\s?% off[^.]{0,120}\.?[^.]{0,60}", text)}
    return [{"firm": "hantec", "kind": "banner", "code": "", "plan_key": "*", "list_price": None,
             "deal_price": None, "pct": float(re.match(r"\d+", b).group()), "terms": b,
             "source": PAGE, "status": "valid"} for b in sorted(found)]


def _check(opener: urllib.request.OpenerDirector, token: str, plan_id: int, code: str,
           field: str) -> float:
    """Dollars Hantec's `CheckDiscount` takes off one plan with the code in one box; 0 if not valid."""
    body = json.dumps({"discountCode": "", "affiliateCode": "", "selectedPlanId": plan_id,
                       field: code}).encode()
    req = urllib.request.Request(f"{PAGE}?handler=CheckDiscount", data=body, headers={
        **UA, "Content-Type": "application/json; charset=utf-8", "RequestVerificationToken": token})
    r = json.load(opener.open(req, timeout=60))
    valid, off = (("validDiscountCode", "discountByDiscountCode") if field == "discountCode"
                  else ("validAffiliateCode", "discountByAffiliateCode"))
    return r[off] if r[valid] else 0


def hantec_code(code: str, source: str) -> list[dict]:
    """Ask Hantec's own `CheckDiscount` what a code takes off each plan; [] when it is not valid.

    The same call the page makes when a code is typed in the box: it validates, it buys nothing.
    A code is tried as a discount code, then as an affiliate code (aggregators publish those).
    """
    opener, _, token = _hantec_session()
    plans = hantec.fetch()["plans"]
    for field in ("discountCode", "affiliateCode"):
        offs = {p["planId"]: _check(opener, token, p["planId"], code, field) for p in plans}
        if any(offs.values()):
            break
    rows = []
    for p in plans:
        off = offs[p["planId"]]
        if not off:
            continue
        key = f"hantec:{p['productCategoryName'].lower().replace(' ', '-')}:{int(p['startingBalance'])}:USD"
        rows.append({"firm": "hantec", "kind": "code", "code": code.upper(), "plan_key": key,
                     "list_price": p["price"], "deal_price": round(p["price"] - off, 2),
                     "pct": round(100 * off / p["price"], 1),
                     "terms": "discount code" if field == "discountCode" else "affiliate code",
                     "source": source, "status": "valid"})
    return rows


def ftmo_table() -> list[dict]:
    """The discounted prices FTMO's pricing table carries, one row per plan it applies to."""
    data = ftmo.fetch()["data"]
    rows = []
    for price_key, (family, _, _) in ftmo.TYPES.items():
        for i, price in enumerate(data["prices"][price_key]):
            if not price["discounted"]:
                continue
            for item in data["items"]:
                size = int(float(item["challenges"][i]["balance"]))
                list_price, deal = float(price["price"]), float(price["discounted_price"])
                rows.append({"firm": "ftmo", "kind": "table", "code": "",
                             "plan_key": f"ftmo:{family}:{size}:{item['currency']}",
                             "list_price": list_price, "deal_price": deal,
                             "pct": round(100 * (1 - deal / list_price), 1),
                             "terms": price["discounted_price_tooltip_text"], "source": ftmo.SOURCE,
                             "status": "valid"})
    return rows


def fundednext_table() -> list[dict]:
    """The sale prices FundedNext's catalogue carries (a crossed-out price, maybe a promo code)."""
    rows = []
    for package in fundednext.fetch()["packages"]:
        for variant in package["challengesSubVariant"]:
            for c in variant["challenges"]:
                if not c.get("originalPrice"):
                    continue
                list_price, deal = fundednext.money(c["originalPrice"]), fundednext.money(c["discountedPrice"])
                rows.append({"firm": "fundednext", "kind": "table", "code": c.get("promoCode") or "",
                             "plan_key": f"fundednext:{package['id']}:{int(c['numericAccountSize'])}:USD",
                             "list_price": list_price, "deal_price": deal,
                             "pct": round(100 * (1 - deal / list_price), 1),
                             "terms": c.get("savedAmount") or "", "source": fundednext.SOURCE,
                             "status": "valid"})
    return rows
