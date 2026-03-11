"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { useParams } from "next/navigation";
import { ArrowLeft, Zap, CheckCircle2, ArrowRight, Phone } from "lucide-react";

/* ──────────────────────────────────────────────
   타입 정의
   ────────────────────────────────────────────── */
type TableRow = { w: string; h: string; d?: string; price: string };

type SubCategory = {
  code: string;
  name: string;
  material: string;
  note?: string;
  columns: string[];
  rows: TableRow[];
};

/* ──────────────────────────────────────────────
   하위 카테고리별 규격+가격 테이블 데이터
   (hkkor.com 실제 데이터 기반)
   ────────────────────────────────────────────── */
const SUB_CATEGORIES: Record<string, SubCategory[]> = {
  "steel-enclosure": [
    {
      code: "HDS",
      name: "옥내노출 분전함",
      material: "스틸 1.6T",
      columns: ["No", "W", "H", "D", "가격(원)"],
      rows: [
        { w: "300", h: "400", d: "150", price: "36,000" },
        { w: "400", h: "500", d: "150", price: "50,000" },
        { w: "400", h: "500", d: "200", price: "59,000" },
        { w: "500", h: "500", d: "150", price: "60,000" },
        { w: "500", h: "600", d: "150", price: "69,000" },
        { w: "500", h: "600", d: "200", price: "70,000" },
        { w: "500", h: "700", d: "150", price: "79,000" },
        { w: "500", h: "700", d: "200", price: "81,000" },
        { w: "500", h: "800", d: "150", price: "84,000" },
        { w: "500", h: "900", d: "150", price: "93,000" },
        { w: "550", h: "600", d: "150", price: "72,000" },
        { w: "600", h: "600", d: "150", price: "80,000" },
        { w: "600", h: "700", d: "150", price: "85,000" },
        { w: "600", h: "700", d: "200", price: "95,000" },
        { w: "600", h: "800", d: "150", price: "103,000" },
        { w: "600", h: "800", d: "200", price: "109,000" },
        { w: "600", h: "900", d: "150", price: "113,000" },
        { w: "600", h: "900", d: "200", price: "120,000" },
        { w: "600", h: "1,000", d: "150", price: "123,000" },
        { w: "600", h: "1,000", d: "200", price: "130,000" },
        { w: "600", h: "1,200", d: "150", price: "160,000" },
        { w: "600", h: "1,200", d: "200", price: "170,000" },
        { w: "700", h: "800", d: "150", price: "115,000" },
        { w: "700", h: "900", d: "150", price: "128,000" },
        { w: "700", h: "900", d: "200", price: "137,000" },
        { w: "700", h: "1,000", d: "150", price: "142,000" },
        { w: "700", h: "1,000", d: "200", price: "153,000" },
        { w: "700", h: "1,200", d: "150", price: "175,000" },
        { w: "700", h: "1,200", d: "200", price: "183,000" },
        { w: "700", h: "1,300", d: "200", price: "200,000" },
        { w: "700", h: "1,400", d: "200", price: "215,000" },
        { w: "700", h: "1,500", d: "200", price: "225,000" },
        { w: "700", h: "1,600", d: "200", price: "243,000" },
        { w: "700", h: "1,800", d: "250", price: "290,000" },
        { w: "800", h: "900", d: "150", price: "142,000" },
        { w: "800", h: "1,000", d: "150", price: "149,000" },
        { w: "800", h: "1,000", d: "150", price: "155,000" },
        { w: "800", h: "1,000", d: "200", price: "159,000" },
        { w: "800", h: "1,200", d: "250", price: "210,000" },
        { w: "800", h: "1,400", d: "250", price: "255,000" },
        { w: "800", h: "1,500", d: "250", price: "270,000" },
        { w: "800", h: "1,800", d: "250", price: "315,000" },
        { w: "900", h: "1,600", d: "250", price: "315,000" },
        { w: "900", h: "1,800", d: "250", price: "345,000" },
        { w: "900", h: "1,800(200)", d: "400", price: "435,000" },
        { w: "900", h: "2,200(200)", d: "400", price: "560,000" },
        { w: "1,000", h: "2,200(200)", d: "400", price: "610,000" },
      ],
    },
    {
      code: "HT",
      name: "옥외노출 분전함",
      material: "스틸 1.6T",
      columns: ["No", "W", "H", "D", "가격(원)"],
      rows: [
        { w: "300", h: "400", d: "150", price: "43,000" },
        { w: "400", h: "500", d: "180", price: "65,000" },
        { w: "500", h: "600", d: "180", price: "80,000" },
        { w: "500", h: "700", d: "180", price: "90,000" },
        { w: "600", h: "600", d: "180", price: "92,000" },
        { w: "600", h: "700", d: "180", price: "100,000" },
        { w: "600", h: "800", d: "180", price: "115,000" },
        { w: "600", h: "900", d: "180", price: "130,000" },
        { w: "700", h: "800", d: "180", price: "135,000" },
        { w: "700", h: "900", d: "180", price: "145,000" },
        { w: "700", h: "1,000", d: "200", price: "166,000" },
        { w: "700", h: "1,200", d: "200", price: "200,000" },
        { w: "800", h: "1,200", d: "200", price: "220,000" },
        { w: "800", h: "1,200", d: "250", price: "230,000" },
      ],
    },
    {
      code: "HB",
      name: "옥내노출 콘트롤 박스",
      material: "스틸 1.0T",
      columns: ["No", "W", "H", "D", "가격(원)"],
      rows: [
        { w: "300", h: "400", d: "150", price: "22,000" },
        { w: "400", h: "500", d: "150", price: "28,000" },
        { w: "400", h: "500", d: "200", price: "29,500" },
        { w: "500", h: "600", d: "150", price: "36,500" },
        { w: "500", h: "600", d: "200", price: "37,800" },
        { w: "600", h: "600", d: "150", price: "53,000" },
        { w: "600", h: "700", d: "150", price: "53,800" },
        { w: "600", h: "700", d: "200", price: "55,800" },
        { w: "600", h: "800", d: "150", price: "60,000" },
        { w: "600", h: "800", d: "200", price: "63,000" },
        { w: "600", h: "900", d: "150", price: "70,000" },
        { w: "600", h: "900", d: "200", price: "74,000" },
        { w: "600", h: "1,000", d: "150", price: "91,000" },
        { w: "700", h: "800", d: "150", price: "80,000" },
        { w: "700", h: "900", d: "150", price: "90,000" },
      ],
    },
    {
      code: "HS",
      name: "매입함",
      material: "스틸 1.6T",
      note: "깊이(D) 고정: 150mm",
      columns: ["No", "W", "H", "가격(원)"],
      rows: [
        { w: "300", h: "400", price: "21,000" },
        { w: "400", h: "400", price: "25,000" },
        { w: "400", h: "500", price: "30,000" },
        { w: "500", h: "500", price: "35,000" },
        { w: "500", h: "600", price: "41,000" },
        { w: "500", h: "700", price: "48,000" },
        { w: "500", h: "800", price: "53,000" },
        { w: "550", h: "600", price: "45,000" },
        { w: "600", h: "600", price: "49,000" },
        { w: "600", h: "700", price: "57,000" },
        { w: "600", h: "800", price: "62,000" },
        { w: "600", h: "900", price: "70,000" },
        { w: "600", h: "1,000", price: "77,000" },
        { w: "600", h: "1,200", price: "95,000" },
        { w: "700", h: "800", price: "73,000" },
        { w: "700", h: "900", price: "81,000" },
        { w: "700", h: "1,000", price: "90,000" },
        { w: "700", h: "1,200", price: "109,000" },
        { w: "800", h: "900", price: "95,000" },
        { w: "800", h: "1,000", price: "105,000" },
        { w: "800", h: "1,200", price: "125,000" },
        { w: "800", h: "1,400", price: "145,000" },
      ],
    },
  ],
  "stainless-enclosure": [
    {
      code: "SHDS",
      name: "옥내노출 분전함",
      material: "SUS 201 1.2T",
      columns: ["No", "W", "H", "D", "가격(원)"],
      rows: [
        { w: "300", h: "400", d: "150", price: "54,000" },
        { w: "300", h: "400", d: "200", price: "60,000" },
        { w: "400", h: "500", d: "150", price: "76,000" },
        { w: "400", h: "500", d: "200", price: "84,000" },
        { w: "500", h: "600", d: "150", price: "107,000" },
        { w: "500", h: "600", d: "200", price: "110,000" },
        { w: "500", h: "700", d: "150", price: "125,000" },
        { w: "500", h: "700", d: "200", price: "128,000" },
        { w: "600", h: "700", d: "150", price: "147,000" },
        { w: "600", h: "700", d: "200", price: "149,000" },
        { w: "600", h: "800", d: "150", price: "168,000" },
        { w: "600", h: "800", d: "200", price: "170,000" },
        { w: "600", h: "900", d: "150", price: "195,000" },
        { w: "600", h: "900", d: "200", price: "197,000" },
        { w: "600", h: "1,000", d: "150", price: "210,000" },
        { w: "600", h: "1,000", d: "200", price: "220,000" },
        { w: "600", h: "1,200", d: "150", price: "248,000" },
        { w: "600", h: "1,200", d: "200", price: "262,000" },
        { w: "700", h: "800", d: "150", price: "200,000" },
        { w: "700", h: "800", d: "200", price: "205,000" },
        { w: "700", h: "900", d: "150", price: "215,000" },
        { w: "700", h: "900", d: "200", price: "220,000" },
        { w: "700", h: "1,000", d: "150", price: "253,000" },
        { w: "700", h: "1,000", d: "200", price: "255,000" },
        { w: "700", h: "1,200", d: "150", price: "275,000" },
        { w: "700", h: "1,200", d: "200", price: "296,000" },
      ],
    },
    {
      code: "SS",
      name: "매입함 커버",
      material: "SUS 201 1.0T",
      note: "깊이(D) 고정: 150mm",
      columns: ["No", "W", "H", "가격(원)"],
      rows: [
        { w: "300", h: "400", price: "23,000" },
        { w: "400", h: "400", price: "25,000" },
        { w: "400", h: "500", price: "29,000" },
        { w: "500", h: "500", price: "33,000" },
        { w: "500", h: "600", price: "37,000" },
        { w: "500", h: "700", price: "42,000" },
        { w: "500", h: "800", price: "48,000" },
        { w: "550", h: "600", price: "41,000" },
        { w: "600", h: "600", price: "42,000" },
        { w: "600", h: "700", price: "48,000" },
        { w: "600", h: "800", price: "52,000" },
        { w: "600", h: "900", price: "58,000" },
        { w: "600", h: "1,000", price: "64,000" },
        { w: "600", h: "1,200", price: "72,000" },
        { w: "700", h: "800", price: "60,000" },
        { w: "700", h: "900", price: "65,000" },
        { w: "700", h: "1,000", price: "71,000" },
        { w: "700", h: "1,200", price: "83,000" },
        { w: "800", h: "900", price: "71,000" },
        { w: "800", h: "1,000", price: "79,000" },
        { w: "800", h: "1,200", price: "95,000" },
        { w: "800", h: "1,400", price: "111,000" },
      ],
    },
    {
      code: "SC",
      name: "옥외노출 분전함",
      material: "SUS 201 1.2T",
      columns: ["No", "W", "H", "D", "가격(원)"],
      rows: [
        { w: "200", h: "300", d: "180", price: "50,000" },
        { w: "300", h: "400", d: "180", price: "73,000" },
        { w: "400", h: "500", d: "180", price: "94,000" },
        { w: "500", h: "600", d: "180", price: "127,000" },
        { w: "500", h: "700", d: "180", price: "141,000" },
        { w: "600", h: "600", d: "180", price: "145,000" },
        { w: "600", h: "700", d: "180", price: "173,000" },
        { w: "600", h: "800", d: "180", price: "193,000" },
        { w: "600", h: "900", d: "180", price: "218,000" },
        { w: "600", h: "1,000", d: "180", price: "248,000" },
        { w: "700", h: "800", d: "180", price: "230,000" },
        { w: "700", h: "900", d: "180", price: "256,000" },
        { w: "700", h: "1,000", d: "200", price: "266,000" },
        { w: "700", h: "1,200", d: "200", price: "320,000" },
      ],
    },
  ],
  "meter-box": [
    {
      code: "CT-1",
      name: "CT-1 계량기함",
      material: "STS 201 1.2T",
      columns: ["No", "W", "H", "D", "가격(원)"],
      rows: [
        { w: "600", h: "800", d: "250", price: "119,900" },
      ],
    },
    {
      code: "CT-2",
      name: "CT-2 계량기함 (200AF 전용)",
      material: "STS 201 1.2T",
      note: "계량기공간 800mm",
      columns: ["No", "W", "H", "D", "가격(원)"],
      rows: [
        { w: "600", h: "1,100", d: "250", price: "169,900" },
      ],
    },
    {
      code: "SCT-단상",
      name: "단상 계량기함",
      material: "STS 201 1.2T",
      note: "계량기공간: 1회로 300mm / 2회로 350mm",
      columns: ["회로수", "W", "H", "D", "가격(원)"],
      rows: [
        { w: "250", h: "600", d: "150", price: "86,000" },
        { w: "400", h: "600", d: "150", price: "120,000" },
      ],
    },
    {
      code: "SCT-3상",
      name: "3상 계량기함",
      material: "STS 201 1.2T",
      columns: ["회로수", "W", "H", "D", "가격(원)"],
      rows: [
        { w: "350", h: "420", d: "200", price: "85,000" },
        { w: "350", h: "700", d: "150", price: "119,900" },
        { w: "550", h: "700", d: "150", price: "180,000" },
        { w: "750", h: "700", d: "150", price: "250,000" },
        { w: "850", h: "800", d: "180", price: "280,000" },
      ],
    },
    {
      code: "SCT-자립",
      name: "자립 계량기함 (옥외자립)",
      material: "STS 201 1.2T",
      note: "베이스 200mm 포함, 계량기공간 800mm",
      columns: ["모델명", "W", "H", "D", "가격(원)"],
      rows: [
        { w: "650", h: "1,400(200)", d: "250", price: "440,000" },
        { w: "700", h: "1,500(200)", d: "250", price: "540,000" },
        { w: "800", h: "1,700(200)", d: "250", price: "699,000" },
        { w: "1,100", h: "2,000(200)", d: "400", price: "1,200,000" },
      ],
    },
    {
      code: "EVHDS",
      name: "전기차 계량기함",
      material: "STS 201 1.2T",
      columns: ["회로수", "W", "H", "D", "가격(원)"],
      rows: [
        { w: "650", h: "800+800", d: "250", price: "310,000" },
        { w: "700", h: "800x900", d: "250", price: "360,000" },
      ],
    },
  ],
  "distribution-panel": [
    {
      code: "NO.1",
      name: "NO.1 (2P) - 메인 SBS-52/50A, 분기 SIE-32/20A x10",
      material: "STEEL 1.0T",
      columns: ["타입", "W", "H", "D", "가격(원)"],
      rows: [
        { w: "400", h: "500", d: "150", price: "200,000" },
        { w: "400", h: "500", d: "150 (매입)", price: "230,000" },
      ],
    },
    {
      code: "NO.2",
      name: "NO.2 (4P) - 메인 SBS-54/50A, 분기 SEC-53/30A x2 + SIE-32/20A x6",
      material: "STEEL 1.0T",
      columns: ["타입", "W", "H", "D", "가격(원)"],
      rows: [
        { w: "500", h: "600", d: "150", price: "250,000" },
        { w: "500", h: "600", d: "150 (매입)", price: "300,000" },
      ],
    },
    {
      code: "NO.3",
      name: "NO.3 (4P) - 메인 SBE-104/75A, 분기 SBC-53 x2 + SEC-52 x2 + SIE-32 x8",
      material: "STEEL 1.0T",
      columns: ["타입", "W", "H", "D", "가격(원)"],
      rows: [
        { w: "500", h: "600", d: "150", price: "280,000" },
        { w: "500", h: "600", d: "150 (매입)", price: "310,000" },
      ],
    },
    {
      code: "NO.4",
      name: "NO.4 (4P) - 메인 SBS-54/50A, 분기 SES-54/30A x2 + SIE-32/20A x8",
      material: "STEEL 1.0T",
      columns: ["타입", "W", "H", "D", "가격(원)"],
      rows: [
        { w: "600", h: "600", d: "150", price: "330,000" },
        { w: "600", h: "600", d: "150 (매입)", price: "360,000" },
      ],
    },
    {
      code: "NO.5",
      name: "NO.5 (4P) - 메인 SBE-104/100A, 분기 SBS-54 x1 + SEC-53 x2 + SIE-32 x10",
      material: "STEEL 1.0T",
      columns: ["타입", "W", "H", "D", "가격(원)"],
      rows: [
        { w: "600", h: "700", d: "150", price: "340,000" },
        { w: "600", h: "700", d: "150 (매입)", price: "390,000" },
      ],
    },
  ],
  "ev-panel": [
    {
      code: "급속-100KW",
      name: "CT계량기 판넬 100KW (급속, 옥외자립)",
      material: "SUS 201 1.2T/1.5T",
      columns: ["회로수", "W", "H", "D", "가격(원)"],
      rows: [
        { w: "650", h: "1,400(200)", d: "250", price: "700,000" },
        { w: "800", h: "1,700(200)", d: "250", price: "1,400,000" },
        { w: "1,100", h: "2,000(200)", d: "400", price: "2,400,000" },
        { w: "1,100", h: "2,000(200)", d: "400", price: "2,700,000" },
      ],
    },
    {
      code: "급속-200KW",
      name: "CT계량기 판넬 200KW (급속, 옥외자립)",
      material: "SUS 201 1.5T",
      columns: ["회로수", "W", "H", "D", "가격(원)"],
      rows: [
        { w: "800", h: "1,700(200)", d: "250", price: "1,250,000" },
        { w: "1,100", h: "2,000(200)", d: "400", price: "2,990,000" },
      ],
    },
    {
      code: "완속-전선",
      name: "계량기 판넬 7KW (완속, 전선처리)",
      material: "STS 201 1.2T/1.5T",
      note: "일반/전기차전용 가격 구분",
      columns: ["회로수", "외함 사이즈", "메인 차단기", "일반(원)", "전기차전용(원)"],
      rows: [
        { w: "300x400x150", h: "-", price: "45,000 / 56,000" },
        { w: "500x600x150", h: "MCCB 4P 50AT", price: "150,000 / 175,000" },
        { w: "500x600x150", h: "MCCB 4P 50AT", price: "170,000 / 205,000" },
        { w: "500x600x150", h: "MCCB 4P 75AT", price: "190,000 / 226,000" },
        { w: "500x700x150", h: "MCCB 4P 75AT", price: "230,000 / 290,000" },
        { w: "600x900x150", h: "MCCB 4P 100AT", price: "270,000 / 340,000" },
        { w: "600x1,000x150", h: "MCCB 4P 100AT", price: "285,000 / 370,000" },
        { w: "600x1,000x150", h: "MCCB 4P 125AT", price: "387,000 / 480,000" },
        { w: "600x1,000x150", h: "MCCB 4P 125AT", price: "415,000 / 520,000" },
        { w: "650x(800+800)x250", h: "MCCB 4P 150AT", price: "660,000 / 780,000" },
        { w: "650x(800+800)x250", h: "MCCB 4P 150AT", price: "690,000 / 820,000" },
        { w: "650x(800+800)x250", h: "MCCB 4P 175AT", price: "720,000 / 860,000" },
        { w: "650x(800+800)x250", h: "MCCB 4P 175AT", price: "750,000 / 900,000" },
        { w: "650x(800+800)x250", h: "MCCB 4P 200AT", price: "770,000 / 940,000" },
        { w: "700x(800+900)x250", h: "MCCB 4P 200AT", price: "840,000 / 1,000,000" },
      ],
    },
    {
      code: "완속-부스바",
      name: "계량기 판넬 7KW (완속, 부스바처리)",
      material: "STS 201 1.2T/1.5T",
      note: "일반/전기차전용 가격 구분",
      columns: ["회로수", "외함 사이즈", "메인 차단기", "일반(원)", "전기차전용(원)"],
      rows: [
        { w: "250x(300+300)x130", h: "-", price: "95,000 / 107,000" },
        { w: "400x(300+500)x150", h: "MCCB 4P 50AT", price: "252,000 / 275,000" },
        { w: "400x(300+500)x150", h: "MCCB 4P 50AT", price: "272,000 / 310,000" },
        { w: "400x(300+500)x150", h: "MCCB 4P 75AT", price: "292,000 / 340,000" },
        { w: "600x(400+600)x150", h: "MCCB 4P 75AT", price: "403,000 / 460,000" },
        { w: "600x(400+600)x150", h: "MCCB 4P 100AT", price: "422,000 / 490,000" },
        { w: "600x(400+600)x150", h: "MCCB 4P 100AT", price: "437,000 / 520,000" },
        { w: "600x(400+600)x150", h: "MCCB 4P 125AT", price: "518,000 / 610,000" },
        { w: "600x(400+600)x150", h: "MCCB 4P 125AT", price: "546,000 / 650,000" },
        { w: "700x(800+700+200)x250", h: "MCCB 4P 150AT", price: "950,000 / 1,080,000" },
        { w: "700x(800+700+200)x250", h: "MCCB 4P 150AT", price: "970,000 / 1,100,000" },
        { w: "700x(800+700+200)x250", h: "MCCB 4P 175AT", price: "990,000 / 1,120,000" },
        { w: "700x(800+900+200)x250", h: "MCCB 4P 175AT", price: "1,060,000 / 1,210,000" },
        { w: "700x(800+900+200)x250", h: "MCCB 4P 200AT", price: "1,080,000 / 1,250,000" },
        { w: "700x(800+900+200)x250", h: "MCCB 4P 200AT", price: "1,120,000 / 1,380,000" },
      ],
    },
  ],
  "solar-panel": [
    {
      code: "30-50KW",
      name: "태양광 30~50KW",
      material: "SUS 201 1.2T (옥외노출)",
      note: "사이즈: 500x(400+500)x200",
      columns: ["브랜드", "가격(원)"],
      rows: [
        { w: "상도", h: "", price: "480,000" },
        { w: "대륙", h: "", price: "540,000" },
        { w: "LS", h: "", price: "640,000" },
      ],
    },
    {
      code: "100KW",
      name: "태양광 100KW",
      material: "SUS 201 1.2T (옥외노출)",
      note: "사이즈: 750x(500+600)x200",
      columns: ["브랜드", "가격(원)"],
      rows: [
        { w: "상도 (메인:대륙)", h: "", price: "1,150,000" },
        { w: "대륙", h: "", price: "1,250,000" },
        { w: "LS", h: "", price: "1,400,000" },
      ],
    },
  ],
};

/* ──────────────────────────────────────────────
   제품 상세 데이터
   ────────────────────────────────────────────── */
const PRODUCT_DATA: Record<string, {
  title: string;
  subtitle: string;
  description: string[];
  specs: { label: string; value: string }[];
  features: string[];
  images: string[];
  priceRange: string;
  priceNote: string;
}> = {
  "steel-enclosure": {
    title: "철 기성함",
    subtitle: "Steel Enclosure",
    description: [
      "SPC(냉간압연강판) 1.0t~1.6t 소재를 사용한 내구성 높은 기성함입니다.",
      "분체도장 처리로 부식을 방지하며, 옥내/옥외 설치 환경에 대응합니다.",
      "HDS(옥내노출), HT(옥외노출), HB(콘트롤박스), HS(매입함) 4종으로 구분됩니다.",
    ],
    specs: [
      { label: "재질", value: "SPC 1.0t~1.6t (냉간압연강판)" },
      { label: "도장", value: "분체도장 (회색/아이보리)" },
      { label: "용도", value: "옥내/옥외" },
      { label: "규격", value: "300x400 ~ 1,000x2,200mm" },
      { label: "방수등급", value: "IP20~IP44" },
    ],
    features: ["KS 표준 규격 준수", "분체도장으로 부식 방지", "4종 타입별 최적 설계", "다양한 크기 즉시 납품", "맞춤 제작 가능"],
    images: ["/images/products/steel1.jpg", "/images/products/steel2.jpg"],
    priceRange: "21,000원 ~ 610,000원",
    priceNote: "규격에 따라 가격이 상이합니다. 아래 가격표를 참고해 주세요.",
  },
  "stainless-enclosure": {
    title: "스테인리스 기성함",
    subtitle: "Stainless Steel Enclosure",
    description: [
      "SUS 201 스테인리스 소재로 뛰어난 내부식성을 자랑합니다.",
      "옥외, 해안가, 화학 환경 등 가혹한 조건에서도 사용 가능합니다.",
      "SHDS(옥내노출), SS(매입함 커버), SC(옥외노출) 3종으로 구분됩니다.",
    ],
    specs: [
      { label: "재질", value: "SUS 201 1.0T~1.2T" },
      { label: "마감", value: "헤어라인 / No.4 피니시" },
      { label: "용도", value: "옥외/옥내 겸용" },
      { label: "규격", value: "200x300 ~ 800x1,400mm" },
      { label: "방수등급", value: "IP44~IP66" },
    ],
    features: ["뛰어난 내부식성", "옥외 설치 가능", "위생 환경 적합", "고급 헤어라인 마감", "IP66 방수 대응"],
    images: ["/images/products/stainless1.jpg", "/images/products/stainless2.jpg"],
    priceRange: "23,000원 ~ 320,000원",
    priceNote: "규격에 따라 가격이 상이합니다. 아래 가격표를 참고해 주세요.",
  },
  "meter-box": {
    title: "계량기함",
    subtitle: "Meter Box",
    description: [
      "한국전력 규격을 준수하는 계량기함입니다.",
      "CT-1, CT-2, 단상, 삼상, 자립형, 전기차 전용 등 다양한 타입을 보유하고 있습니다.",
      "옥외 방수 설계로 다양한 환경에서 안정적으로 사용할 수 있습니다.",
    ],
    specs: [
      { label: "재질", value: "STS 201 1.2T" },
      { label: "용도", value: "단상 / 삼상 / 전기차" },
      { label: "규격", value: "한전 표준 규격" },
      { label: "방수등급", value: "IP44 이상" },
      { label: "잠금", value: "한전 전용 잠금장치" },
    ],
    features: ["한전 규격 100% 준수", "CT-1/CT-2/자립형 등 다양한 타입", "옥외 방수 설계", "전용 잠금장치", "전국 즉시 납품"],
    images: ["/images/products/meter1.jpg", "/images/products/meter2.jpg"],
    priceRange: "85,000원 ~ 1,200,000원",
    priceNote: "타입 및 규격에 따라 가격이 상이합니다. 아래 가격표를 참고해 주세요.",
  },
  "distribution-panel": {
    title: "기성 분전반",
    subtitle: "Distribution Panel",
    description: [
      "IEC 61439, KS C 4510 표준을 준수하는 기성 분전반입니다.",
      "주택, 상가, 사무실 등 다양한 용도에 대응합니다.",
      "NO.1(2P)~NO.5(4P)까지 5가지 표준 모델을 보유하고 있습니다.",
    ],
    specs: [
      { label: "규격", value: "IEC 61439 / KS C 4510" },
      { label: "차단기", value: "MCCB / ELB" },
      { label: "전압", value: "220V / 380V" },
      { label: "설치", value: "노출함 / 매입함" },
      { label: "재질", value: "STEEL 1.0T" },
    ],
    features: ["IEC/KS 국제 표준 준수", "노출함/매입함 선택 가능", "5가지 표준 모델", "즉시 납품 가능", "맞춤 제작 대응"],
    images: ["/images/products/panel1.jpg", "/images/about/intro2.webp"],
    priceRange: "200,000원 ~ 390,000원",
    priceNote: "모델 및 설치 타입에 따라 가격이 상이합니다. 아래 가격표를 참고해 주세요.",
  },
  "ev-panel": {
    title: "전기차 분전반",
    subtitle: "EV Charging Panel",
    description: [
      "전기차 충전 인프라 전용으로 설계된 분전반입니다.",
      "급속(100KW/200KW) 및 완속(7KW) 충전기에 대응합니다.",
      "전선처리/부스바처리 방식을 선택할 수 있습니다.",
    ],
    specs: [
      { label: "재질", value: "SUS 201 1.2T/1.5T" },
      { label: "충전", value: "급속/완속 대응" },
      { label: "전압", value: "380V 3상" },
      { label: "안전", value: "누전차단 + 서지보호" },
      { label: "설치", value: "옥외 자립형" },
    ],
    features: ["급속 100KW/200KW 대응", "완속 7KW 전선/부스바 처리", "누전차단기 필수 탑재", "서지보호장치 포함", "CT 계량기 일체형"],
    images: ["/images/products/ev1.jpg", "/images/products/ev2.jpg"],
    priceRange: "45,000원 ~ 2,990,000원",
    priceNote: "충전 타입, 회로수에 따라 가격이 상이합니다. 아래 가격표를 참고해 주세요.",
  },
  "solar-panel": {
    title: "태양광 분전반",
    subtitle: "Solar Power Panel",
    description: [
      "태양광 발전 시스템에 최적화된 분전반입니다.",
      "인버터 연동 설계로 계통연계에 적합하며, 역전력 보호 기능을 갖추고 있습니다.",
      "30~50KW, 100KW 2가지 타입을 보유하고 있습니다.",
    ],
    specs: [
      { label: "재질", value: "SUS 201 1.2T" },
      { label: "연동", value: "인버터 연동" },
      { label: "보호", value: "역전력 보호 / SPD" },
      { label: "설치", value: "옥외 노출형" },
      { label: "브랜드", value: "상도 / 대륙 / LS" },
    ],
    features: ["인버터 연동 설계", "역전력 보호 기능", "계통연계 최적화", "SPD 서지보호", "브랜드별 가격 선택"],
    images: ["/images/products/solar1.png", "/images/products/solar2.jpg"],
    priceRange: "480,000원 ~ 1,400,000원",
    priceNote: "용량 및 브랜드에 따라 가격이 상이합니다. 아래 가격표를 참고해 주세요.",
  },
};

/* ──────────────────────────────────────────────
   렌더링 헬퍼: 테이블 컴포넌트
   ────────────────────────────────────────────── */
function PriceTable({ sub, slug }: { sub: SubCategory; slug: string }) {
  const isEvSlow = slug === "ev-panel" && (sub.code === "완속-전선" || sub.code === "완속-부스바");
  const isSolar = slug === "solar-panel";

  return (
    <div>
      {sub.note && (
        <p className="text-xs text-gray-500 mb-3">{sub.note}</p>
      )}
      <div className="overflow-x-auto rounded-xl border border-gray-200">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-[#0F172A] text-white">
              {sub.columns.map((col) => (
                <th key={col} className="px-4 py-3 text-left font-semibold text-[13px] whitespace-nowrap">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sub.rows.map((row, i) => (
              <tr
                key={i}
                className={`${i % 2 === 0 ? "bg-white" : "bg-gray-50"} hover:bg-blue-50/50 transition-colors`}
              >
                <td className="px-4 py-2.5 text-gray-900 font-medium whitespace-nowrap">{i + 1}</td>
                {isEvSlow ? (
                  <>
                    <td className="px-4 py-2.5 text-gray-600 whitespace-nowrap">{row.w}</td>
                    <td className="px-4 py-2.5 text-gray-600 whitespace-nowrap">{row.h}</td>
                    {row.price.includes("/") ? (
                      <>
                        <td className="px-4 py-2.5 font-bold text-red-600 whitespace-nowrap">{row.price.split(" / ")[0]}</td>
                        <td className="px-4 py-2.5 font-bold text-blue-600 whitespace-nowrap">{row.price.split(" / ")[1]}</td>
                      </>
                    ) : (
                      <td colSpan={2} className="px-4 py-2.5 font-bold text-red-600 whitespace-nowrap">{row.price}</td>
                    )}
                  </>
                ) : isSolar ? (
                  <>
                    <td className="px-4 py-2.5 text-gray-600 whitespace-nowrap">{row.w}</td>
                    <td className="px-4 py-2.5 font-bold text-red-600 whitespace-nowrap text-right">{row.price}</td>
                  </>
                ) : (
                  <>
                    <td className="px-4 py-2.5 text-gray-600 whitespace-nowrap">{row.w}</td>
                    <td className="px-4 py-2.5 text-gray-600 whitespace-nowrap">{row.h}</td>
                    {row.d !== undefined && (
                      <td className="px-4 py-2.5 text-gray-600 whitespace-nowrap">{row.d}</td>
                    )}
                    <td className="px-4 py-2.5 font-bold text-red-600 whitespace-nowrap text-right">{row.price}</td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────
   메인 페이지 컴포넌트
   ────────────────────────────────────────────── */
export default function ProductDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const product = PRODUCT_DATA[slug];
  const subCategories = SUB_CATEGORIES[slug];
  const [activeTab, setActiveTab] = useState(0);

  if (!product) {
    return (
      <div className="pt-[99px] min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-slate-900 mb-4">제품을 찾을 수 없습니다</h1>
          <Link href="/products" className="text-red-600 hover:underline">제품 목록으로 돌아가기</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="pt-[99px]">
      {/* Hero */}
      <section className="bg-[#0B1120] py-16 sm:py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <Link href="/products" className="inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-white mb-6 transition-colors">
            <ArrowLeft className="w-4 h-4" /> 전체 제품
          </Link>
          <p className="text-sm font-bold text-red-400 tracking-[0.15em] uppercase">{product.subtitle}</p>
          <h1 className="mt-2 font-heading text-3xl sm:text-4xl lg:text-5xl font-bold text-white tracking-tight">{product.title}</h1>
        </div>
      </section>

      {/* 상세 내용 */}
      <section className="py-16 sm:py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
            {/* 왼쪽: 이미지 + 설명 + 가격표 (8칸) */}
            <div className="lg:col-span-8 space-y-10">
              {/* 제품 이미지 갤러리 */}
              <div className="grid grid-cols-2 gap-4">
                {product.images.map((img, i) => (
                  <div key={i} className="relative aspect-square bg-gray-50 rounded-2xl overflow-hidden border border-gray-100">
                    <Image src={img} alt={`${product.title} ${i + 1}`} fill className="object-contain p-6" />
                  </div>
                ))}
              </div>

              {/* 제품 설명 */}
              <div>
                <h2 className="font-heading text-2xl font-bold text-gray-900 mb-6">제품 설명</h2>
                <div className="space-y-4">
                  {product.description.map((p, i) => (
                    <p key={i} className="text-gray-500 leading-relaxed text-[15px]">{p}</p>
                  ))}
                </div>
              </div>

              {/* 제품 사양 테이블 */}
              <div>
                <h2 className="font-heading text-2xl font-bold text-gray-900 mb-6">제품 사양</h2>
                <div className="bg-gray-50 rounded-2xl border border-gray-100 overflow-hidden">
                  {product.specs.map((spec, i) => (
                    <div key={spec.label} className={`flex items-center justify-between px-6 py-4 ${i < product.specs.length - 1 ? "border-b border-gray-100" : ""}`}>
                      <span className="text-sm font-medium text-gray-400 w-28 shrink-0">{spec.label}</span>
                      <span className="text-sm font-semibold text-gray-900 text-right">{spec.value}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* ★ 하위 카테고리별 규격·가격표 */}
              {subCategories && subCategories.length > 0 && (
                <div>
                  <h2 className="font-heading text-2xl font-bold text-gray-900 mb-2">규격 · 가격표</h2>
                  <p className="text-sm text-gray-400 mb-6">단위: mm / 가격: 원 (부가세 별도)</p>

                  {/* 탭 네비게이션 */}
                  {subCategories.length > 1 && (
                    <div className="flex flex-wrap gap-2 mb-6">
                      {subCategories.map((sub, idx) => (
                        <button
                          key={sub.code}
                          onClick={() => setActiveTab(idx)}
                          className={`px-4 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                            activeTab === idx
                              ? "bg-[#0F172A] text-white shadow-md"
                              : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                          }`}
                        >
                          {sub.code}
                          <span className="ml-1.5 text-xs font-normal opacity-70">{sub.name}</span>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* 선택된 탭의 테이블 */}
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <h3 className="font-heading text-lg font-bold text-gray-800">
                        {subCategories[activeTab].code} - {subCategories[activeTab].name}
                      </h3>
                      <span className="text-xs text-gray-400 bg-gray-100 px-2.5 py-1 rounded-md">
                        {subCategories[activeTab].material}
                      </span>
                      <span className="text-xs text-gray-400">
                        {subCategories[activeTab].rows.length}개 모델
                      </span>
                    </div>

                    <PriceTable sub={subCategories[activeTab]} slug={slug} />
                  </div>
                </div>
              )}

              {/* 주요 특징 */}
              <div>
                <h2 className="font-heading text-2xl font-bold text-gray-900 mb-6">주요 특징</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {product.features.map((f) => (
                    <div key={f} className="flex items-center gap-3 bg-gray-50 rounded-xl px-5 py-4 border border-gray-100">
                      <CheckCircle2 className="w-5 h-5 text-red-600 shrink-0" />
                      <span className="text-sm font-medium text-gray-700">{f}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* 오른쪽: 가격 + CTA — sticky (4칸) */}
            <div className="lg:col-span-4">
              <div className="lg:sticky lg:top-[120px] space-y-6">
                <div className="bg-gray-50 rounded-2xl p-6 border border-gray-100">
                  <p className="text-sm text-gray-400 font-medium mb-2">가격</p>
                  <p className="font-heading text-2xl font-bold text-red-600 mb-3">{product.priceRange}</p>
                  <p className="text-xs text-gray-400 leading-relaxed">{product.priceNote}</p>
                </div>

                <Link
                  href="/estimate"
                  className="flex items-center justify-center gap-2 w-full px-6 py-4 rounded-xl text-base font-bold bg-red-600 text-white hover:bg-red-500 transition-all hover:shadow-lg active:scale-[0.98]"
                >
                  <Zap className="w-5 h-5" />
                  AI 견적 받기
                </Link>

                <Link
                  href="/support/contact"
                  className="flex items-center justify-center gap-2 w-full px-6 py-3.5 rounded-xl text-sm font-semibold text-gray-700 border border-gray-200 hover:bg-gray-50 transition-all"
                >
                  문의하기 <ArrowRight className="w-4 h-4" />
                </Link>

                <a
                  href="tel:053-792-1410"
                  className="flex items-center justify-center gap-2 w-full px-6 py-3.5 rounded-xl text-sm font-semibold text-gray-500 hover:text-gray-700 transition-colors"
                >
                  <Phone className="w-4 h-4" /> 053-792-1410
                </a>

                <div className="bg-[#0F172A] rounded-2xl p-6 text-white">
                  <p className="text-xs text-slate-400 font-medium uppercase tracking-wider mb-4">Quick Spec</p>
                  {product.specs.slice(0, 3).map((spec) => (
                    <div key={spec.label} className="flex justify-between py-2.5 border-b border-white/[0.06] last:border-0">
                      <span className="text-sm text-slate-400">{spec.label}</span>
                      <span className="text-sm font-semibold text-white">{spec.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
