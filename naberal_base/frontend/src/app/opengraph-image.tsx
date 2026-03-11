import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "한국산업 이앤에스 - 분전반·기성함 전문기업";
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
          background: "linear-gradient(135deg, #1E3A8A 0%, #1E40AF 50%, #3B82F6 100%)",
          position: "relative",
        }}
      >
        {/* Grid pattern overlay */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            opacity: 0.08,
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.3) 1px, transparent 1px)",
            backgroundSize: "60px 60px",
          }}
        />

        {/* Company Name */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "16px",
          }}
        >
          <div
            style={{
              fontSize: "28px",
              color: "#93C5FD",
              fontWeight: 500,
              letterSpacing: "6px",
            }}
          >
            HANKOOK INDUSTRY E&S
          </div>
          <div
            style={{
              fontSize: "56px",
              fontWeight: 800,
              color: "white",
              lineHeight: 1.2,
              textAlign: "center",
            }}
          >
            ㈜한국산업 이앤에스
          </div>
          <div
            style={{
              fontSize: "24px",
              color: "#BFDBFE",
              fontWeight: 400,
              marginTop: "8px",
            }}
          >
            분전반 · 기성함 전문 제조기업
          </div>
        </div>

        {/* Divider */}
        <div
          style={{
            width: "120px",
            height: "4px",
            background: "#F59E0B",
            borderRadius: "2px",
            marginTop: "32px",
            marginBottom: "32px",
          }}
        />

        {/* Features */}
        <div
          style={{
            display: "flex",
            gap: "40px",
            alignItems: "center",
          }}
        >
          {["AI 견적 시스템", "IEC/KS 표준", "전국 배송"].map((text) => (
            <div
              key={text}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                color: "#E0E7FF",
                fontSize: "20px",
              }}
            >
              <div
                style={{
                  width: "8px",
                  height: "8px",
                  background: "#F59E0B",
                  borderRadius: "50%",
                }}
              />
              {text}
            </div>
          ))}
        </div>

        {/* URL */}
        <div
          style={{
            position: "absolute",
            bottom: "32px",
            fontSize: "18px",
            color: "#93C5FD",
            letterSpacing: "2px",
          }}
        >
          hkkor.com
        </div>
      </div>
    ),
    { ...size }
  );
}
