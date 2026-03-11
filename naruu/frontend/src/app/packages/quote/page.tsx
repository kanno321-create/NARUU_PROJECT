"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type {
  Package,
  PackageListResponse,
  QuoteRequest,
  QuoteResponse,
  CurrencyType,
  RecommendResponse,
} from "@/lib/types";

interface CartItem {
  pkg: Package;
  quantity: number;
  customPrice?: number;
}

export default function QuotePage() {
  const [packages, setPackages] = useState<Package[]>([]);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [targetCurrency, setTargetCurrency] = useState<CurrencyType>("JPY");
  const [customerName, setCustomerName] = useState("");
  const [notes, setNotes] = useState("");
  const [discount, setDiscount] = useState(0);
  const [quote, setQuote] = useState<QuoteResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchInput, setSearchInput] = useState("");

  // AI Recommendation
  const [showRecommend, setShowRecommend] = useState(false);
  const [recommendTags, setRecommendTags] = useState("");
  const [recommendBudget, setRecommendBudget] = useState("");
  const [recommendInterests, setRecommendInterests] = useState("");
  const [recommendation, setRecommendation] = useState<RecommendResponse | null>(null);
  const [aiLoading, setAiLoading] = useState(false);

  const quoteRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await api.get<PackageListResponse>("/packages?per_page=100");
        setPackages(data.items);
      } catch (err) {
        console.error("Failed to load packages:", err);
      }
    })();
  }, []);

  const filteredPackages = packages.filter(
    (p) =>
      !searchInput ||
      p.name_ja.toLowerCase().includes(searchInput.toLowerCase()) ||
      p.name_ko.toLowerCase().includes(searchInput.toLowerCase())
  );

  const addToCart = (pkg: Package) => {
    setCart((prev) => {
      const existing = prev.find((c) => c.pkg.id === pkg.id);
      if (existing) {
        return prev.map((c) =>
          c.pkg.id === pkg.id ? { ...c, quantity: c.quantity + 1 } : c
        );
      }
      return [...prev, { pkg, quantity: 1 }];
    });
  };

  const updateQuantity = (pkgId: number, qty: number) => {
    if (qty <= 0) {
      setCart((prev) => prev.filter((c) => c.pkg.id !== pkgId));
    } else {
      setCart((prev) =>
        prev.map((c) => (c.pkg.id === pkgId ? { ...c, quantity: qty } : c))
      );
    }
  };

  const removeFromCart = (pkgId: number) => {
    setCart((prev) => prev.filter((c) => c.pkg.id !== pkgId));
  };

  const generateQuote = async () => {
    if (cart.length === 0) return;
    setLoading(true);
    try {
      const body: QuoteRequest = {
        items: cart.map((c) => ({
          package_id: c.pkg.id,
          quantity: c.quantity,
          custom_price: c.customPrice,
        })),
        target_currency: targetCurrency,
        customer_name: customerName || undefined,
        notes: notes || undefined,
        discount_percent: discount,
      };
      const data = await api.post<QuoteResponse>("/packages/quote", body);
      setQuote(data);
    } catch (err) {
      console.error("Quote failed:", err);
      alert("견적 생성에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const getRecommendation = async () => {
    setAiLoading(true);
    try {
      const data = await api.post<RecommendResponse>("/packages/recommend", {
        customer_tags: recommendTags
          ? recommendTags.split(",").map((t) => t.trim())
          : undefined,
        budget_jpy: recommendBudget ? Number(recommendBudget) : undefined,
        interests: recommendInterests || undefined,
      });
      setRecommendation(data);

      // Auto-add recommended packages to cart
      if (data.suggested_package_ids.length > 0) {
        const suggestedPkgs = packages.filter((p) =>
          data.suggested_package_ids.includes(p.id)
        );
        for (const pkg of suggestedPkgs) {
          if (!cart.find((c) => c.pkg.id === pkg.id)) {
            addToCart(pkg);
          }
        }
      }
    } catch (err) {
      console.error("Recommendation failed:", err);
      alert("AI 추천에 실패했습니다.");
    } finally {
      setAiLoading(false);
    }
  };

  const printQuote = () => {
    if (!quoteRef.current) return;
    const printWindow = window.open("", "_blank");
    if (!printWindow) return;
    printWindow.document.write(`
      <html>
        <head>
          <title>NARUU 견적서</title>
          <style>
            body { font-family: 'Noto Sans JP', 'Noto Sans KR', sans-serif; padding: 40px; color: #333; }
            h1 { color: #2563eb; font-size: 24px; border-bottom: 2px solid #2563eb; padding-bottom: 10px; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
            th { background: #f3f4f6; font-weight: 600; }
            .total-row { font-weight: bold; background: #eff6ff; }
            .info { margin-bottom: 20px; color: #666; }
            .footer { margin-top: 40px; font-size: 12px; color: #999; text-align: center; }
            @media print { body { padding: 20px; } }
          </style>
        </head>
        <body>
          ${quoteRef.current.innerHTML}
          <div class="footer">
            NARUU（ナル）- 大邱美容観光・医療観光<br/>
            この見積書は参考価格であり、最終金額は変更される場合がございます。
          </div>
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.print();
  };

  const formatPrice = (amount: number, currency: string) => {
    if (currency === "JPY") return `¥${amount.toLocaleString()}`;
    return `₩${amount.toLocaleString()}`;
  };

  return (
    <AppShell>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">견적서 생성</h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Package Picker */}
        <div className="lg:col-span-1 space-y-4">
          {/* AI Recommendation Toggle */}
          <div className="bg-gradient-to-r from-violet-50 to-blue-50 rounded-xl p-4 shadow-sm">
            <button
              onClick={() => setShowRecommend(!showRecommend)}
              className="w-full text-left font-semibold text-violet-700 text-sm"
            >
              AI 패키지 추천 {showRecommend ? "▲" : "▼"}
            </button>
            {showRecommend && (
              <div className="mt-3 space-y-2">
                <input
                  type="text"
                  value={recommendTags}
                  onChange={(e) => setRecommendTags(e.target.value)}
                  placeholder="고객 태그 (쉼표 구분: VIP, 성형)"
                  className="w-full px-3 py-1.5 border border-violet-200 rounded-lg text-sm outline-none focus:ring-1 focus:ring-violet-400"
                />
                <input
                  type="number"
                  value={recommendBudget}
                  onChange={(e) => setRecommendBudget(e.target.value)}
                  placeholder="예산 (JPY)"
                  className="w-full px-3 py-1.5 border border-violet-200 rounded-lg text-sm outline-none focus:ring-1 focus:ring-violet-400"
                />
                <input
                  type="text"
                  value={recommendInterests}
                  onChange={(e) => setRecommendInterests(e.target.value)}
                  placeholder="관심사 (예: 피부과, 대구관광)"
                  className="w-full px-3 py-1.5 border border-violet-200 rounded-lg text-sm outline-none focus:ring-1 focus:ring-violet-400"
                />
                <button
                  onClick={getRecommendation}
                  disabled={aiLoading}
                  className="w-full py-2 bg-violet-600 text-white rounded-lg text-sm hover:bg-violet-700 disabled:opacity-50"
                >
                  {aiLoading ? "AI 분석 중..." : "추천 받기"}
                </button>
                {recommendation && (
                  <div className="mt-2 p-3 bg-white rounded-lg text-xs text-gray-700 whitespace-pre-wrap max-h-48 overflow-y-auto">
                    {recommendation.recommendation}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Package Search & List */}
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="패키지 검색..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm mb-3 outline-none focus:ring-2 focus:ring-naruu-500"
            />
            <div className="max-h-96 overflow-y-auto space-y-2">
              {filteredPackages.map((pkg) => {
                const inCart = cart.some((c) => c.pkg.id === pkg.id);
                return (
                  <div
                    key={pkg.id}
                    className={`flex items-center justify-between p-3 rounded-lg border text-sm ${
                      inCart
                        ? "border-naruu-300 bg-naruu-50"
                        : "border-gray-200 hover:border-naruu-300 hover:bg-gray-50"
                    } cursor-pointer transition`}
                    onClick={() => addToCart(pkg)}
                  >
                    <div>
                      <p className="font-medium text-gray-800">{pkg.name_ja}</p>
                      <p className="text-xs text-gray-500">{pkg.name_ko}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-mono text-gray-700">
                        {pkg.base_price
                          ? formatPrice(pkg.base_price, pkg.currency)
                          : "-"}
                      </p>
                      {inCart && (
                        <span className="text-xs text-naruu-600">추가됨</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right: Cart & Quote */}
        <div className="lg:col-span-2 space-y-4">
          {/* Cart */}
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <h3 className="font-semibold text-gray-700 mb-4">선택한 패키지</h3>
            {cart.length === 0 ? (
              <p className="text-sm text-gray-400 py-4 text-center">
                왼쪽에서 패키지를 선택하세요
              </p>
            ) : (
              <div className="space-y-3">
                {cart.map((item) => (
                  <div
                    key={item.pkg.id}
                    className="flex items-center gap-4 p-3 border border-gray-200 rounded-lg"
                  >
                    <div className="flex-1">
                      <p className="font-medium text-sm text-gray-800">
                        {item.pkg.name_ja}
                      </p>
                      <p className="text-xs text-gray-500">
                        {item.pkg.base_price
                          ? formatPrice(item.pkg.base_price, item.pkg.currency)
                          : "-"}{" "}
                        / 개
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => updateQuantity(item.pkg.id, item.quantity - 1)}
                        className="w-7 h-7 flex items-center justify-center border border-gray-300 rounded text-sm hover:bg-gray-50"
                      >
                        -
                      </button>
                      <span className="w-8 text-center text-sm font-medium">
                        {item.quantity}
                      </span>
                      <button
                        onClick={() => updateQuantity(item.pkg.id, item.quantity + 1)}
                        className="w-7 h-7 flex items-center justify-center border border-gray-300 rounded text-sm hover:bg-gray-50"
                      >
                        +
                      </button>
                    </div>
                    <button
                      onClick={() => removeFromCart(item.pkg.id)}
                      className="text-red-400 hover:text-red-600 text-sm"
                    >
                      삭제
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Quote Options */}
          <div className="bg-white rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="font-semibold text-gray-700">견적 옵션</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-600 mb-1">고객명</label>
                <input
                  type="text"
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-naruu-500"
                  placeholder="田中 太郎"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">표시 통화</label>
                <select
                  value={targetCurrency}
                  onChange={(e) => setTargetCurrency(e.target.value as CurrencyType)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-naruu-500"
                >
                  <option value="JPY">¥ JPY (엔)</option>
                  <option value="KRW">₩ KRW (원)</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-600 mb-1">할인율 (%)</label>
                <input
                  type="number"
                  value={discount}
                  onChange={(e) => setDiscount(Number(e.target.value) || 0)}
                  min={0}
                  max={100}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-naruu-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">비고</label>
                <input
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-naruu-500"
                  placeholder="특이사항..."
                />
              </div>
            </div>

            <button
              onClick={generateQuote}
              disabled={loading || cart.length === 0}
              className="w-full py-3 bg-naruu-600 text-white rounded-lg font-medium hover:bg-naruu-700 disabled:opacity-50 transition"
            >
              {loading ? "견적 생성 중..." : "견적서 생성"}
            </button>
          </div>

          {/* Generated Quote */}
          {quote && (
            <div className="bg-white rounded-xl p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-700">견적서 미리보기</h3>
                <button
                  onClick={printQuote}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm font-medium"
                >
                  PDF / 인쇄
                </button>
              </div>

              {/* Printable Content */}
              <div ref={quoteRef}>
                <h1>NARUU お見積書</h1>
                {quote.customer_name && (
                  <div className="info">
                    <p>
                      <strong>{quote.customer_name}</strong> 様
                    </p>
                    <p>
                      発行日:{" "}
                      {new Date(quote.generated_at).toLocaleDateString("ja-JP")}
                    </p>
                  </div>
                )}

                <table>
                  <thead>
                    <tr>
                      <th>パッケージ名</th>
                      <th>カテゴリ</th>
                      <th style={{ textAlign: "right" }}>単価</th>
                      <th style={{ textAlign: "center" }}>数量</th>
                      <th style={{ textAlign: "right" }}>小計</th>
                    </tr>
                  </thead>
                  <tbody>
                    {quote.line_items.map((item, i) => (
                      <tr key={i}>
                        <td>{item.package_name_ja}</td>
                        <td>{item.category}</td>
                        <td style={{ textAlign: "right", fontFamily: "monospace" }}>
                          {formatPrice(item.unit_price, item.currency)}
                        </td>
                        <td style={{ textAlign: "center" }}>{item.quantity}</td>
                        <td style={{ textAlign: "right", fontFamily: "monospace" }}>
                          {formatPrice(item.subtotal, item.currency)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr>
                      <td colSpan={4} style={{ textAlign: "right" }}>
                        小計
                      </td>
                      <td
                        style={{ textAlign: "right", fontFamily: "monospace" }}
                      >
                        {formatPrice(quote.subtotal, "JPY")}
                      </td>
                    </tr>
                    {quote.discount_percent > 0 && (
                      <tr>
                        <td colSpan={4} style={{ textAlign: "right", color: "#dc2626" }}>
                          割引 ({quote.discount_percent}%)
                        </td>
                        <td
                          style={{
                            textAlign: "right",
                            fontFamily: "monospace",
                            color: "#dc2626",
                          }}
                        >
                          -{formatPrice(quote.discount_amount, "JPY")}
                        </td>
                      </tr>
                    )}
                    <tr className="total-row">
                      <td colSpan={4} style={{ textAlign: "right", fontWeight: "bold" }}>
                        合計
                      </td>
                      <td
                        style={{
                          textAlign: "right",
                          fontFamily: "monospace",
                          fontWeight: "bold",
                          fontSize: "1.1em",
                        }}
                      >
                        {formatPrice(quote.total, "JPY")}
                      </td>
                    </tr>
                    {quote.total_converted && quote.exchange_rate && (
                      <tr>
                        <td
                          colSpan={5}
                          style={{
                            textAlign: "right",
                            color: "#666",
                            fontSize: "0.9em",
                          }}
                        >
                          参考: {formatPrice(quote.total_converted, quote.converted_currency || "KRW")}{" "}
                          (レート: 1 JPY = {quote.exchange_rate.toFixed(2)} KRW)
                        </td>
                      </tr>
                    )}
                  </tfoot>
                </table>

                {quote.notes && (
                  <div className="info">
                    <p>
                      <strong>備考:</strong> {quote.notes}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
