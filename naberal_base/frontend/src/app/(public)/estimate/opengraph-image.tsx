import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "AI 분전반 견적 - 30초 만에 견적 완성";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          background: "linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #1E40AF 100%)",
        }}
      >
        {/* Badge */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "8px 20px",
            background: "rgba(245, 158, 11, 0.15)",
            borderRadius: "24px",
            marginBottom: "24px",
          }}
        >
          <div
            style={{
              width: "10px",
              height: "10px",
              background: "#F59E0B",
              borderRadius: "50%",
            }}
          />
          <span style={{ color: "#FCD34D", fontSize: "18px", fontWeight: 600 }}>
            AI 기반 자동 견적
          </span>
        </div>

        {/* Title */}
        <div
          style={{
            fontSize: "52px",
            fontWeight: 800,
            color: "white",
            textAlign: "center",
            lineHeight: 1.3,
          }}
        >
          30초 만에 정확한
        </div>
        <div
          style={{
            fontSize: "52px",
            fontWeight: 800,
            color: "#60A5FA",
            textAlign: "center",
            lineHeight: 1.3,
          }}
        >
          분전반 견적 완성
        </div>

        {/* Steps */}
        <div
          style={{
            display: "flex",
            gap: "32px",
            marginTop: "40px",
            alignItems: "center",
          }}
        >
          {[
            { step: "1", label: "용도 선택" },
            { step: "2", label: "차단기 구성" },
            { step: "3", label: "견적 확인" },
          ].map((item, i) => (
            <div
              key={item.step}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
              }}
            >
              <div
                style={{
                  width: "40px",
                  height: "40px",
                  borderRadius: "50%",
                  background: "#3B82F6",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "white",
                  fontSize: "18px",
                  fontWeight: 700,
                }}
              >
                {item.step}
              </div>
              <span style={{ color: "#CBD5E1", fontSize: "20px" }}>
                {item.label}
              </span>
              {i < 2 && (
                <span style={{ color: "#475569", fontSize: "24px", marginLeft: "8px" }}>
                  →
                </span>
              )}
            </div>
          ))}
        </div>

        {/* Footer */}
        <div
          style={{
            position: "absolute",
            bottom: "32px",
            display: "flex",
            alignItems: "center",
            gap: "16px",
          }}
        >
          <span style={{ fontSize: "18px", color: "#64748B" }}>
            ㈜한국산업 이앤에스
          </span>
          <span style={{ color: "#334155" }}>|</span>
          <span style={{ fontSize: "18px", color: "#93C5FD" }}>hkkor.com</span>
        </div>
      </div>
    ),
    { ...size }
  );
}
