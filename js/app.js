(() => {
  const $ = (s) => document.querySelector(s);
  const C = STORE_CONFIG;
  const money = (n) => `${n.toFixed(3).replace(/\.?0+$/, "")} ${C.currency}`;

  // ---------- الحالة ----------
  let cart = load();
  let activeCat = "all";
  let query = "";

  function load() {
    try { return JSON.parse(localStorage.getItem("cart") || "{}"); } catch { return {}; }
  }
  function save() {
    try { localStorage.setItem("cart", JSON.stringify(cart)); } catch {}
  }

  // ---------- العناصر الثابتة ----------
  $("#storeName").textContent = C.name;
  document.querySelectorAll(".store-name").forEach((e) => (e.textContent = C.name));
  $("#tagline").textContent = C.tagline;
  $("#year").textContent = new Date().getFullYear();
  $("#topbar").textContent = `🎁 شحن مجاني للطلبات فوق ${money(C.freeShippingFrom)} — الدفع عند الاستلام متاح`;

  // ---------- التصنيفات ----------
  function renderCats() {
    $("#cats").innerHTML = CATEGORIES.map((c) =>
      `<button class="cat ${c.id === activeCat ? "active" : ""}" data-cat="${c.id}">${c.icon} ${c.name}</button>`
    ).join("");
  }
  $("#cats").addEventListener("click", (e) => {
    const b = e.target.closest("[data-cat]");
    if (!b) return;
    activeCat = b.dataset.cat;
    renderCats(); renderGrid();
  });

  // ---------- المنتجات ----------
  const discount = (p) => (p.oldPrice ? Math.round((1 - p.price / p.oldPrice) * 100) : 0);

  function renderGrid() {
    const q = query.trim();
    const list = PRODUCTS.filter((p) =>
      (activeCat === "all" || p.cat === activeCat) &&
      (!q || p.name.includes(q) || p.desc.includes(q)));
    $("#empty").hidden = list.length > 0;
    $("#grid").innerHTML = list.map((p) => `
      <article class="card" data-id="${p.id}">
        ${p.badge ? `<span class="badge">${p.badge}</span>` : ""}
        <div class="thumb" data-view>${p.icon}</div>
        <div class="card-body">
          <h3 data-view>${p.name}</h3>
          <div class="rating">⭐ ${p.rating} <span>(${p.sold}+ مبيع)</span></div>
          <div class="price">
            <strong>${money(p.price)}</strong>
            ${p.oldPrice ? `<s>${money(p.oldPrice)}</s>` : ""}
          </div>
          <button class="btn btn-primary btn-block" data-add>أضف للسلة</button>
        </div>
      </article>`).join("");
  }
  $("#grid").addEventListener("click", (e) => {
    const card = e.target.closest(".card");
    if (!card) return;
    const id = +card.dataset.id;
    if (e.target.closest("[data-add]")) add(id);
    else if (e.target.closest("[data-view]")) openProduct(id);
  });
  $("#search").addEventListener("input", (e) => { query = e.target.value; renderGrid(); });

  function openProduct(id) {
    const p = PRODUCTS.find((x) => x.id === id);
    $("#productBody").innerHTML = `
      <div class="product-view">
        <div class="thumb big">${p.icon}</div>
        <div>
          <h2>${p.name}</h2>
          <div class="rating">⭐ ${p.rating} <span>(${p.sold}+ عميل اشترى هذا المنتج)</span></div>
          <div class="price big">
            <strong>${money(p.price)}</strong>
            ${p.oldPrice ? `<s>${money(p.oldPrice)}</s> <em>وفّر ${discount(p)}%</em>` : ""}
          </div>
          <p>${p.desc}</p>
          <ul class="perks"><li>✔ ضمان استبدال</li><li>✔ الدفع عند الاستلام</li><li>✔ تتبع الشحنة</li></ul>
          <button class="btn btn-primary btn-block" id="modalAdd">أضف للسلة</button>
        </div>
      </div>`;
    $("#modalAdd").onclick = () => { add(id); close($("#productModal")); };
    open($("#productModal"));
  }

  // ---------- السلة ----------
  function add(id) {
    cart[id] = (cart[id] || 0) + 1;
    save(); renderCart();
    toast("تمت الإضافة إلى السلة ✅");
  }
  function setQty(id, q) {
    if (q <= 0) delete cart[id]; else cart[id] = q;
    save(); renderCart();
  }
  function totals() {
    const items = Object.entries(cart)
      .map(([id, qty]) => ({ p: PRODUCTS.find((x) => x.id === +id), qty }))
      .filter((i) => i.p);
    const subtotal = items.reduce((s, i) => s + i.p.price * i.qty, 0);
    const shipping = subtotal === 0 || subtotal >= C.freeShippingFrom ? 0 : C.shippingFee;
    return { items, subtotal, shipping };
  }
  function renderCart() {
    const { items, subtotal, shipping } = totals();
    $("#cartCount").textContent = items.reduce((s, i) => s + i.qty, 0);
    $("#checkout").hidden = items.length === 0;
    if (!items.length) {
      $("#cartItems").innerHTML = `<p class="empty">السلة فارغة 🛒</p>`;
      $("#cartSummary").innerHTML = "";
      return;
    }
    $("#cartItems").innerHTML = items.map(({ p, qty }) => `
      <div class="cart-item" data-id="${p.id}">
        <div class="thumb sm">${p.icon}</div>
        <div class="ci-info"><b>${p.name}</b><span>${money(p.price)}</span></div>
        <div class="qty">
          <button data-q="-1">−</button><span>${qty}</span><button data-q="1">+</button>
        </div>
      </div>`).join("");
    const left = C.freeShippingFrom - subtotal;
    $("#cartSummary").innerHTML = `
      ${left > 0 ? `<div class="hint">أضف ${money(left)} للحصول على شحن مجاني 🚚</div>` : `<div class="hint ok">🎉 حصلت على شحن مجاني</div>`}
      <div class="row"><span>المجموع</span><span>${money(subtotal)}</span></div>
      <div class="row"><span>الشحن</span><span>${shipping ? money(shipping) : "مجاني"}</span></div>
      <div class="row total"><span>الإجمالي</span><span>${money(subtotal + shipping)}</span></div>`;
  }
  $("#cartItems").addEventListener("click", (e) => {
    const b = e.target.closest("[data-q]");
    if (!b) return;
    const id = +b.closest(".cart-item").dataset.id;
    setQty(id, (cart[id] || 0) + +b.dataset.q);
  });

  // ---------- إتمام الطلب عبر واتساب ----------
  $("#checkout").addEventListener("submit", (e) => {
    e.preventDefault();
    const f = Object.fromEntries(new FormData(e.target));
    const { items, subtotal, shipping } = totals();
    const cod = f.pay === "cod" ? C.codFee : 0;
    const orderId = "R" + Date.now().toString().slice(-6);
    const lines = [
      `🛍️ طلب جديد #${orderId} — ${C.name}`,
      "",
      ...items.map(({ p, qty }) => `• ${p.name} × ${qty} = ${money(p.price * qty)}`),
      "",
      `المجموع: ${money(subtotal)}`,
      `الشحن: ${shipping ? money(shipping) : "مجاني"}`,
      cod ? `رسوم الدفع عند الاستلام: ${money(cod)}` : null,
      `الإجمالي: ${money(subtotal + shipping + cod)}`,
      "",
      `الاسم: ${f.name}`,
      `الجوال: ${f.phone}`,
      `العنوان: ${f.country} - ${f.city} - ${f.address}`,
      `الدفع: ${f.pay === "cod" ? "عند الاستلام" : "تحويل بنكي"}`,
    ].filter((l) => l !== null);
    window.open(`https://wa.me/${C.whatsapp}?text=${encodeURIComponent(lines.join("\n"))}`, "_blank");
    cart = {}; save(); renderCart(); e.target.reset();
    close($("#cart"));
    toast(`تم تجهيز طلبك #${orderId} — أكمل الإرسال في واتساب`);
  });

  // ---------- النوافذ ----------
  function open(el) { el.hidden = false; document.body.style.overflow = "hidden"; }
  function close(el) { el.hidden = true; document.body.style.overflow = ""; }
  $("#openCart").addEventListener("click", () => open($("#cart")));
  document.querySelectorAll(".modal, .drawer").forEach((el) =>
    el.addEventListener("click", (e) => {
      if (e.target === el || e.target.closest("[data-close]")) close(el);
    }));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") document.querySelectorAll(".modal, .drawer").forEach(close);
  });

  let tt;
  function toast(msg) {
    const t = $("#toast");
    t.textContent = msg; t.classList.add("show");
    clearTimeout(tt); tt = setTimeout(() => t.classList.remove("show"), 2200);
  }

  renderCats(); renderGrid(); renderCart();
})();
