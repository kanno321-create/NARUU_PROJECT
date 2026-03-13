"use client";

import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import AppShell from "@/components/layout/app-shell";
import { api } from "@/lib/api";
import type {
  OrderItem, OrderListResponse, OrderSummary,
  ExpenseItem, ExpenseListResponse, ExpenseSummary,
  PnLReport,
} from "@/lib/types";
import { PAYMENT_STATUS_LABELS, PAYMENT_STATUS_COLORS, PIE_COLORS } from "@/lib/constants";
import LoadingSpinner from "@/components/ui/loading-spinner";
import ErrorBanner from "@/components/ui/error-banner";

export default function FinancePage() {
  const [tab, setTab] = useState<"overview" | "revenue" | "expense">("overview");
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [pnl, setPnl] = useState<PnLReport | null>(null);
  const [orderSummary, setOrderSummary] = useState<OrderSummary | null>(null);
  const [expenseSummary, setExpenseSummary] = useState<ExpenseSummary | null>(null);
  const [orders, setOrders] = useState<OrderItem[]>([]);
  const [expenses, setExpenses] = useState<ExpenseItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New expense form
  const [showExpenseForm, setShowExpenseForm] = useState(false);
  const [expForm, setExpForm] = useState({ category: "", vendor_name: "", amount: "", description: "" });
  const [savingExpense, setSavingExpense] = useState(false);

  useEffect(() => { loadData(); }, [year, month]);

  async function loadData() {
    setLoading(true);
    try {
      const [p, os, es, ol, el] = await Promise.all([
        api.get<PnLReport>(`/expenses/pnl?year=${year}&month=${month}`),
        api.get<OrderSummary>(`/orders/summary?year=${year}&month=${month}`),
        api.get<ExpenseSummary>(`/expenses/summary?year=${year}&month=${month}`),
        api.get<OrderListResponse>(`/orders?per_page=10`),
        api.get<ExpenseListResponse>(`/expenses?per_page=10`),
      ]);
      setPnl(p);
      setOrderSummary(os);
      setExpenseSummary(es);
      setOrders(ol.items);
      setExpenses(el.items);
      setError(null);
    } catch {
      setError("데이터를 불러오는데 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  async function handleAddExpense(e: React.FormEvent) {
    e.preventDefault();
    if (!expForm.category || !expForm.vendor_name || !expForm.amount) return;

    setSavingExpense(true);
    try {
      await api.post("/expenses", {
        category: expForm.category,
        vendor_name: expForm.vendor_name,
        amount: parseFloat(expForm.amount),
        description: expForm.description || undefined,
      });
      setExpForm({ category: "", vendor_name: "", amount: "", description: "" });
      setShowExpenseForm(false);
      loadData();
    } catch (err) {
      setError("등록 실패: " + (err instanceof Error ? err.message : "알 수 없는 오류"));
    } finally {
      setSavingExpense(false);
    }
  }

  const pnlBarData = pnl
    ? [
        { name: "매출(총)", value: pnl.revenue.gross },
        { name: "커미션", value: pnl.revenue.commission },
        { name: "순매출", value: pnl.revenue.net },
        { name: "매입", value: pnl.expenses },
        { name: "이익", value: pnl.profit },
      ]
    : [];

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">매출/매입 관리</h2>
        <div className="flex gap-2 items-center">
          <label htmlFor="finance-year" className="sr-only">연도</label>
          <select id="finance-year" value={year} onChange={(e) => setYear(Number(e.target.value))} className="px-3 py-2 border border-gray-200 rounded-lg text-sm" aria-label="연도 선택">
            {[2024, 2025, 2026].map((y) => <option key={y} value={y}>{y}년</option>)}
          </select>
          <label htmlFor="finance-month" className="sr-only">월</label>
          <select id="finance-month" value={month} onChange={(e) => setMonth(Number(e.target.value))} className="px-3 py-2 border border-gray-200 rounded-lg text-sm" aria-label="월 선택">
            {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => <option key={m} value={m}>{m}월</option>)}
          </select>
        </div>
      </div>

      <ErrorBanner message={error} />

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 rounded-lg p-1 w-fit" role="tablist" aria-label="재무 탭">
        {[
          { key: "overview", label: "손익 개요" },
          { key: "revenue", label: "매출 (주문)" },
          { key: "expense", label: "매입 (경비)" },
        ].map((t) => (
          <button
            key={t.key}
            role="tab"
            aria-selected={tab === t.key}
            onClick={() => setTab(t.key as typeof tab)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition ${
              tab === t.key ? "bg-white shadow text-naruu-700" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <LoadingSpinner text="데이터 로딩 중..." />
      ) : tab === "overview" ? (
        /* P&L Overview */
        <div className="space-y-6">
          {pnl && (
            <>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="bg-white rounded-xl p-4 shadow-sm">
                  <p className="text-xs text-gray-500 mb-1">총 매출</p>
                  <p className="text-xl font-bold text-gray-800">{pnl.revenue.gross.toLocaleString()}</p>
                </div>
                <div className="bg-white rounded-xl p-4 shadow-sm">
                  <p className="text-xs text-gray-500 mb-1">커미션</p>
                  <p className="text-xl font-bold text-orange-600">-{pnl.revenue.commission.toLocaleString()}</p>
                </div>
                <div className="bg-white rounded-xl p-4 shadow-sm">
                  <p className="text-xs text-gray-500 mb-1">순 매출</p>
                  <p className="text-xl font-bold text-blue-600">{pnl.revenue.net.toLocaleString()}</p>
                </div>
                <div className="bg-white rounded-xl p-4 shadow-sm">
                  <p className="text-xs text-gray-500 mb-1">총 매입</p>
                  <p className="text-xl font-bold text-red-600">-{pnl.expenses.toLocaleString()}</p>
                </div>
                <div className={`rounded-xl p-4 shadow-sm ${pnl.profit >= 0 ? "bg-green-50" : "bg-red-50"}`}>
                  <p className="text-xs text-gray-500 mb-1">순이익</p>
                  <p className={`text-xl font-bold ${pnl.profit >= 0 ? "text-green-700" : "text-red-700"}`}>
                    {pnl.profit.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-400">마진 {pnl.profit_margin}%</p>
                </div>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-sm">
                <h3 className="font-semibold text-gray-700 mb-4">{year}년 {month}월 손익 구조</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={pnlBarData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip formatter={(v: any) => v.toLocaleString()} />
                    <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]}>
                      {pnlBarData.map((entry, i) => (
                        <Cell
                          key={i}
                          fill={
                            entry.name === "이익"
                              ? entry.value >= 0 ? "#22c55e" : "#ef4444"
                              : entry.name === "커미션" || entry.name === "매입"
                              ? "#f59e0b"
                              : "#6366f1"
                          }
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          )}

          {/* Expense by category pie */}
          {expenseSummary && expenseSummary.by_category.length > 0 && (
            <div className="bg-white rounded-xl p-6 shadow-sm">
              <h3 className="font-semibold text-gray-700 mb-4">매입 카테고리별</h3>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={expenseSummary.by_category}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={90}
                    dataKey="total"
                    nameKey="category"
                    label={(props: any) => `${props.category} ${Number(props.total).toLocaleString()}`}
                  >
                    {expenseSummary.by_category.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v: any) => v.toLocaleString()} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      ) : tab === "revenue" ? (
        /* Revenue / Orders */
        <div className="space-y-4">
          {orderSummary && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white rounded-xl p-4 shadow-sm">
                <p className="text-xs text-gray-500 mb-1">총 주문</p>
                <p className="text-2xl font-bold">{orderSummary.total_orders}건</p>
              </div>
              <div className="bg-white rounded-xl p-4 shadow-sm">
                <p className="text-xs text-gray-500 mb-1">결제 완료</p>
                <p className="text-2xl font-bold text-green-600">{orderSummary.paid_orders}건</p>
              </div>
              <div className="bg-white rounded-xl p-4 shadow-sm">
                <p className="text-xs text-gray-500 mb-1">대기 중</p>
                <p className="text-2xl font-bold text-yellow-600">{orderSummary.pending_orders}건</p>
              </div>
              <div className="bg-white rounded-xl p-4 shadow-sm">
                <p className="text-xs text-gray-500 mb-1">순매출</p>
                <p className="text-xl font-bold text-naruu-700">{orderSummary.net_revenue.toLocaleString()}</p>
              </div>
            </div>
          )}

          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600">
                <tr>
                  <th className="px-4 py-3 text-left font-medium">주문 ID</th>
                  <th className="px-4 py-3 text-left font-medium">고객 ID</th>
                  <th className="px-4 py-3 text-right font-medium">금액</th>
                  <th className="px-4 py-3 text-center font-medium">상태</th>
                  <th className="px-4 py-3 text-right font-medium">커미션</th>
                  <th className="px-4 py-3 text-left font-medium">일시</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {orders.length === 0 ? (
                  <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">주문 내역이 없습니다.</td></tr>
                ) : orders.map((o) => (
                  <tr key={o.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono">#{o.id}</td>
                    <td className="px-4 py-3 font-mono">#{o.customer_id}</td>
                    <td className="px-4 py-3 text-right font-medium">{o.total_amount.toLocaleString()} {o.currency}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-xs px-2 py-1 rounded-full ${PAYMENT_STATUS_COLORS[o.payment_status]}`}>
                        {PAYMENT_STATUS_LABELS[o.payment_status]}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right text-orange-600">
                      {o.commission_amount ? o.commission_amount.toLocaleString() : "-"}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500">{new Date(o.created_at).toLocaleDateString("ko-KR")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* Expenses */
        <div className="space-y-4">
          <div className="flex justify-end">
            <button
              onClick={() => setShowExpenseForm(!showExpenseForm)}
              className="px-4 py-2 bg-naruu-600 text-white rounded-lg hover:bg-naruu-700 transition text-sm font-medium"
            >
              + 매입 등록
            </button>
          </div>

          {showExpenseForm && (
            <form onSubmit={handleAddExpense} className="bg-white rounded-xl p-6 shadow-sm space-y-3">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div>
                  <label htmlFor="exp-category" className="sr-only">카테고리</label>
                  <input
                    id="exp-category"
                    type="text"
                    placeholder="카테고리 (교통비, 식비 등)"
                    value={expForm.category}
                    onChange={(e) => setExpForm({ ...expForm, category: e.target.value })}
                    className="px-3 py-2 border border-gray-200 rounded-lg text-sm w-full"
                    required
                    aria-label="카테고리"
                  />
                </div>
                <div>
                  <label htmlFor="exp-vendor" className="sr-only">거래처</label>
                  <input
                    id="exp-vendor"
                    type="text"
                    placeholder="업체/거래처명"
                    value={expForm.vendor_name}
                    onChange={(e) => setExpForm({ ...expForm, vendor_name: e.target.value })}
                    className="px-3 py-2 border border-gray-200 rounded-lg text-sm w-full"
                    required
                    aria-label="거래처"
                  />
                </div>
                <div>
                  <label htmlFor="exp-amount" className="sr-only">금액</label>
                  <input
                    id="exp-amount"
                    type="number"
                    placeholder="금액"
                    value={expForm.amount}
                    onChange={(e) => setExpForm({ ...expForm, amount: e.target.value })}
                    className="px-3 py-2 border border-gray-200 rounded-lg text-sm w-full"
                    required
                    aria-label="금액"
                  />
                </div>
                <div>
                  <label htmlFor="exp-desc" className="sr-only">설명</label>
                  <input
                    id="exp-desc"
                    type="text"
                    placeholder="설명 (선택)"
                    value={expForm.description}
                    onChange={(e) => setExpForm({ ...expForm, description: e.target.value })}
                    className="px-3 py-2 border border-gray-200 rounded-lg text-sm w-full"
                    aria-label="설명"
                  />
                </div>
              </div>
              <button
                type="submit"
                disabled={savingExpense}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 text-sm"
              >
                {savingExpense ? "저장 중..." : "등록"}
              </button>
            </form>
          )}

          {expenseSummary && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="bg-white rounded-xl p-4 shadow-sm">
                <p className="text-xs text-gray-500 mb-1">총 매입</p>
                <p className="text-2xl font-bold text-red-600">{expenseSummary.total_expenses.toLocaleString()}</p>
              </div>
              <div className="bg-white rounded-xl p-4 shadow-sm">
                <p className="text-xs text-gray-500 mb-1">건수</p>
                <p className="text-2xl font-bold">{expenseSummary.expense_count}건</p>
              </div>
              <div className="bg-white rounded-xl p-4 shadow-sm">
                <p className="text-xs text-gray-500 mb-1">카테고리수</p>
                <p className="text-2xl font-bold">{expenseSummary.by_category.length}</p>
              </div>
            </div>
          )}

          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600">
                <tr>
                  <th className="px-4 py-3 text-left font-medium">카테고리</th>
                  <th className="px-4 py-3 text-left font-medium">거래처</th>
                  <th className="px-4 py-3 text-right font-medium">금액</th>
                  <th className="px-4 py-3 text-left font-medium">설명</th>
                  <th className="px-4 py-3 text-left font-medium">일시</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {expenses.length === 0 ? (
                  <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">매입 내역이 없습니다.</td></tr>
                ) : expenses.map((exp) => (
                  <tr key={exp.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-700">{exp.category}</span>
                    </td>
                    <td className="px-4 py-3">{exp.vendor_name}</td>
                    <td className="px-4 py-3 text-right font-medium text-red-600">{exp.amount.toLocaleString()} {exp.currency}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs max-w-xs truncate">{exp.description || "-"}</td>
                    <td className="px-4 py-3 text-xs text-gray-500">{new Date(exp.created_at).toLocaleDateString("ko-KR")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </AppShell>
  );
}
