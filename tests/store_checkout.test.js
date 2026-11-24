// Checkout regression test for the store (Playwright + Chromium).
// Run:  node tests/store_checkout.test.js
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const ROOT = path.resolve(__dirname, '..');
const INDEX = 'file://' + path.join(ROOT, 'index.html');
let failures = 0;
const check = (name, cond, detail = '') => {
  console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${detail ? '  — ' + detail : ''}`);
  if (!cond) failures++;
};

async function openStore(browser, whatsapp) {
  const ctx = await browser.newContext();
  const sent = [];
  ctx.on('request', (r) => { if (r.url().startsWith('https://wa.me/')) sent.push(r.url()); });
  await ctx.route('https://wa.me/**', (r) => r.fulfill({ status: 200, body: 'ok' })); // no real network
  if (whatsapp !== undefined) {
    // serve products.js with a test phone number instead of the placeholder
    const src = fs.readFileSync(path.join(ROOT, 'js/products.js'), 'utf8')
      .replace(/whatsapp:\s*"[^"]*"/, `whatsapp: "${whatsapp}"`);
    await ctx.route('**/js/products.js', (r) => r.fulfill({ body: src, contentType: 'text/javascript' }));
  }
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(INDEX);
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  return { ctx, page, sent, errors };
}

async function fillAndSubmit(page) {
  await page.locator('.card[data-id="1"] [data-add]').click();   // 9.9
  await page.locator('.card[data-id="2"] [data-add]').click();   // 18.5  → free shipping
  await page.click('#openCart');
  for (const [n, v] of [['name', 'Test'], ['phone', '91234567'], ['city', 'Ibri'], ['address', 'Street 1']]) {
    await page.fill(`input[name=${n}]`, v);
  }
}

(async () => {
  const browser = await chromium.launch();

  // 1) placeholder number → order refused, cart kept
  {
    const { ctx, page, sent, errors } = await openStore(browser);
    await fillAndSubmit(page);
    await page.click('#checkout button[type=submit]');
    await page.waitForTimeout(400);
    check('placeholder number: nothing sent to WhatsApp', sent.length === 0, `${sent.length} request(s)`);
    check('placeholder number: cart kept', (await page.textContent('#cartCount')) === '2');
    check('placeholder number: warning shown', (await page.textContent('#toast')).includes('غير مفعّل'));
    check('no page errors (placeholder)', errors.length === 0, errors.join(' | '));
    await ctx.close();
  }

  // 2) valid number → totals consistent (incl. COD fee) and cart cleared only after WhatsApp opens
  {
    const { ctx, page, sent, errors } = await openStore(browser, '96891234567');
    await fillAndSubmit(page);
    const shownCod = (await page.textContent('.cart-summary .total')).replace(/\s+/g, ' ');
    check('cart shows COD fee row', (await page.textContent('#cartSummary')).includes('رسوم الدفع عند الاستلام'));
    check('cart total includes COD fee (28.9)', shownCod.includes('28.9'), shownCod);
    await page.check('input[name=pay][value=transfer]');
    const shownTransfer = (await page.textContent('.cart-summary .total')).replace(/\s+/g, ' ');
    check('switching to bank transfer removes the fee (28.4)', shownTransfer.includes('28.4'), shownTransfer);
    await page.check('input[name=pay][value=cod]');

    const popupP = ctx.waitForEvent('page');
    await page.click('#checkout button[type=submit]');
    await popupP;
    await page.waitForTimeout(300);
    const msg = decodeURIComponent((sent[0] || '').split('text=')[1] || '');
    const msgTotal = (msg.split('\n').find((l) => l.startsWith('الإجمالي')) || '');
    check('order sent to configured number', (sent[0] || '').startsWith('https://wa.me/96891234567'));
    check('message total equals cart total', msgTotal.includes('28.9'), msgTotal);
    check('cart cleared after WhatsApp opened', (await page.textContent('#cartCount')) === '0');
    check('no page errors (valid number)', errors.length === 0, errors.join(' | '));
    await ctx.close();
  }

  await browser.close();
  console.log(failures ? `\n${failures} check(s) failed` : '\nall checks passed');
  process.exit(failures ? 1 : 0);
})();
