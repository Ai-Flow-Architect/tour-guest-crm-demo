"""通しテスト: python3 e2e_test.py [URL]（既定はローカルの index.html）。スクショは _shots/ へ。"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

here = Path(__file__).parent
url = sys.argv[1] if len(sys.argv) > 1 else (here / "index.html").as_uri()
shots = here / "_shots"
shots.mkdir(exist_ok=True)
results = []
errors = []


def check(name, cond):
    results.append((name, bool(cond)))
    print(("OK  " if cond else "NG  ") + name)


with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1366, "height": 900})
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    pg.goto(url)
    pg.wait_for_timeout(800)

    # 1 ゲスト画面が見本入りで開く
    check("ゲスト一覧8名", pg.locator("[data-guest].row").count() == 8)
    check("AI要約が出る", "中村駅" in pg.locator(".ai").inner_text())
    pg.screenshot(path=str(shots / "01_guest.png"), full_page=True)

    # 2 原文ボタンで元メールがハイライト
    pg.locator(".ai .src").first.click()
    pg.wait_for_timeout(500)
    check("原文ハイライト", pg.locator("#mail-m3 mark").count() >= 1)
    pg.screenshot(path=str(shots / "02_source.png"))

    # 3 検索
    pg.fill("#q", "lukas")
    check("検索で1件", pg.locator("[data-guest].row").count() == 1)
    pg.fill("#q", "")

    # 4 担当なしのゲスト → 自分が対応する → 下書き → 送信
    pg.locator('[data-guest="g2"].row').click()
    check("担当なしは返信欄ロック", pg.locator("#reply").is_disabled())
    pg.click('[data-act="claim"]')
    pg.click('[data-act="draft"]')
    check("AI下書きが入る", "IBAN" in pg.input_value("#reply"))
    before = pg.locator("#app .mail").count()
    pg.click('[data-act="send"]')
    pg.wait_for_timeout(300)
    check("送信で履歴+1", pg.locator("#app .mail").count() == before + 1)
    check("送信で返信済", "返信済" in pg.locator(".d-head").inner_text())

    # 5 二重対応防止：山本で佐藤担当のゲストを開くとロック
    pg.select_option("#role", "yamamoto")
    pg.locator('[data-guest="g1"].row').click()
    check("他人担当はロック表示", "佐藤さんが対応中" in pg.locator(".lock").inner_text())
    check("他人担当は返信欄無効", pg.locator("#reply").is_disabled())
    pg.screenshot(path=str(shots / "03_lock.png"))

    # 6 ゲスト→ツアー→ゲストの相互リンク
    pg.locator(".tour-chip").first.click()
    check("ツアー詳細へ遷移", "四万十川カヌー" in pg.locator(".d-head h1").inner_text())
    check("参加ゲスト3組", pg.locator("tbody button[data-guest]").count() == 3)
    pg.screenshot(path=str(shots / "04_tour.png"), full_page=True)
    pg.locator('tbody button[data-guest="g5"]').click()
    check("ツアー→ゲストへ戻れる", "James Carter" in pg.locator(".d-head h1").inner_text())

    # 7 年間50本
    pg.click("#tab-tours")
    pg.select_option("#tf", "all")
    check("年間50本", pg.locator("[data-tour].row").count() == 50)

    # 8 共通メール
    pg.click("#tab-inbox")
    check("受信箱8行", pg.locator(".inbox-row").count() == 8)
    check("返信漏れ注意あり", pg.locator("text=返信漏れ注意").count() >= 1)
    pg.screenshot(path=str(shots / "05_inbox.png"), full_page=True)

    # 9 ガイド権限：ガイド画面以外が閉じる・メール/入金は出ない
    pg.select_option("#role", "tanaka")
    pg.wait_for_timeout(300)
    check("ガイドはタブ1つ", pg.locator("nav.tabs button:visible").count() == 1)
    phone = pg.locator(".phone").inner_text()
    check("ガイドに担当ツアー", "四万十川カヌー" in phone and "仁淀ブルー" in phone)
    check("ガイドに入金・メールなし", "入金" not in phone and "@" not in phone)
    check("ガイドに注意事項", "ナッツアレルギー" in phone)
    check("2日間ツアーの日付が11/14〜11/15", "11/14（土）〜11/15（日）" in phone)
    pg.screenshot(path=str(shots / "06_guide.png"), full_page=True)

    # 10 スマホ幅で横スクロールなし
    m = b.new_page(viewport={"width": 390, "height": 844})
    m.goto(url + "#guide")
    m.wait_for_timeout(600)
    sw = m.evaluate("document.documentElement.scrollWidth")
    check(f"スマホ幅で横はみ出しなし({sw})", sw <= 391)
    m.screenshot(path=str(shots / "07_phone_guide.png"), full_page=True)
    m.goto(url + "#g1")
    m.wait_for_timeout(600)
    sw = m.evaluate("document.documentElement.scrollWidth")
    check(f"スマホ幅 ゲスト画面 横はみ出しなし({sw})", sw <= 391)
    m.screenshot(path=str(shots / "08_phone_guest.png"), full_page=True)

    # 11 ダークモード
    d = b.new_page(viewport={"width": 1366, "height": 900}, color_scheme="dark")
    d.goto(url)
    d.wait_for_timeout(600)
    d.screenshot(path=str(shots / "09_dark.png"))
    b.close()

check("JSエラー0件" + (f" {errors}" if errors else ""), not errors)
ng = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(ng)}/{len(results)} 合格")
sys.exit(1 if ng else 0)
