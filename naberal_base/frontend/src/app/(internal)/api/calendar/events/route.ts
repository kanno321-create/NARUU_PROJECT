import { NextRequest, NextResponse } from "next/server";

/**
 * Calendar Events API Route Handler
 *
 * Proxies all calendar requests to the FastAPI backend at /v1/calendar/events.
 * The backend stores events in PostgreSQL with per-user isolation and sharing.
 *
 * Frontend calls:
 *   /api/calendar/events  ->  this handler  ->  backend /v1/calendar/events
 */

const BACKEND_URL =
    process.env.NEXT_PUBLIC_API_URL || "https://naberalproject-production.up.railway.app";

function backendUrl(path: string, params?: URLSearchParams): string {
    const base = `${BACKEND_URL}/v1/calendar${path}`;
    if (params && params.toString()) {
        return `${base}?${params.toString()}`;
    }
    return base;
}

// GET: 이벤트 목록 조회
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);

        // Convert frontend year/month params to backend start_date/end_date
        const year = searchParams.get("year");
        const month = searchParams.get("month");
        const userId = searchParams.get("user_id") || "default";

        const backendParams = new URLSearchParams();
        backendParams.set("user_id", userId);

        if (year && month) {
            const y = parseInt(year);
            const m = parseInt(month);
            const startDate = `${y}-${String(m).padStart(2, "0")}-01`;
            const lastDay = new Date(y, m, 0).getDate();
            const endDate = `${y}-${String(m).padStart(2, "0")}-${String(lastDay).padStart(2, "0")}`;
            backendParams.set("start_date", startDate);
            backendParams.set("end_date", endDate);
        }

        // Pass through other filters
        const passThroughParams = ["type", "customer", "completed", "limit", "offset", "start_date", "end_date"];
        for (const p of passThroughParams) {
            const val = searchParams.get(p);
            if (val !== null && !backendParams.has(p)) {
                backendParams.set(p, val);
            }
        }

        const url = backendUrl("/events", backendParams);
        const response = await fetch(url, {
            method: "GET",
            headers: { "Content-Type": "application/json" },
        });

        if (!response.ok) {
            const errText = await response.text();
            console.error("Backend GET error:", response.status, errText);
            return NextResponse.json(
                { success: false, error: "Backend fetch failed", events: [] },
                { status: response.status }
            );
        }

        const events = await response.json();

        // Backend returns list[CalendarEvent] directly.
        // Wrap in { success, events, total } for frontend compatibility.
        return NextResponse.json({
            success: true,
            events: events,
            total: events.length,
        });
    } catch (error) {
        console.error("Calendar GET proxy error:", error);
        return NextResponse.json(
            { success: false, error: "Failed to fetch events", events: [] },
            { status: 500 }
        );
    }
}

// POST: 새 이벤트 생성
export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const userId = body.user_id || "default";

        // Map frontend field names to backend expected fields
        const backendBody = {
            title: body.title,
            start: body.start,
            end: body.end || body.start,
            description: body.description,
            location: body.location,
            type: body.type || "meeting",
            priority: body.priority || "normal",
            customer: body.customer,
            estimate_id: body.estimate_id,
            color: body.color,
            all_day: body.all_day || false,
        };

        const params = new URLSearchParams({ user_id: userId });
        const url = backendUrl("/events", params);

        const response = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(backendBody),
        });

        if (!response.ok) {
            const errText = await response.text();
            console.error("Backend POST error:", response.status, errText);
            return NextResponse.json(
                { success: false, error: "Backend create failed" },
                { status: response.status }
            );
        }

        const event = await response.json();
        return NextResponse.json({
            success: true,
            event: event,
        });
    } catch (error) {
        console.error("Calendar POST proxy error:", error);
        return NextResponse.json(
            { success: false, error: "Failed to create event" },
            { status: 500 }
        );
    }
}

// PUT: 이벤트 수정
export async function PUT(request: NextRequest) {
    try {
        const body = await request.json();
        const { id, user_id, ...updates } = body;

        if (!id) {
            return NextResponse.json(
                { success: false, error: "Event ID required" },
                { status: 400 }
            );
        }

        const userId = user_id || "default";

        // Map field names for backend compatibility
        const backendBody: Record<string, unknown> = {};
        if (updates.title !== undefined) backendBody.title = updates.title;
        if (updates.start !== undefined) backendBody.start = updates.start;
        if (updates.end !== undefined) backendBody.end = updates.end;
        if (updates.description !== undefined) backendBody.description = updates.description;
        if (updates.location !== undefined) backendBody.location = updates.location;
        if (updates.type !== undefined) backendBody.type = updates.type;
        if (updates.priority !== undefined) backendBody.priority = updates.priority;
        if (updates.completed !== undefined) backendBody.completed = updates.completed;
        if (updates.customer !== undefined) backendBody.customer = updates.customer;
        if (updates.color !== undefined) backendBody.color = updates.color;
        if (updates.all_day !== undefined) backendBody.all_day = updates.all_day;

        const params = new URLSearchParams({ user_id: userId });
        const url = backendUrl(`/events/${id}`, params);

        const response = await fetch(url, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(backendBody),
        });

        if (!response.ok) {
            const errText = await response.text();
            console.error("Backend PUT error:", response.status, errText);
            return NextResponse.json(
                { success: false, error: "Backend update failed" },
                { status: response.status }
            );
        }

        const event = await response.json();
        return NextResponse.json({
            success: true,
            event: event,
        });
    } catch (error) {
        console.error("Calendar PUT proxy error:", error);
        return NextResponse.json(
            { success: false, error: "Failed to update event" },
            { status: 500 }
        );
    }
}

// DELETE: 이벤트 삭제
export async function DELETE(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const id = searchParams.get("id");
        const userId = searchParams.get("user_id") || "default";

        if (!id) {
            return NextResponse.json(
                { success: false, error: "Event ID required" },
                { status: 400 }
            );
        }

        const params = new URLSearchParams({ user_id: userId });
        const url = backendUrl(`/events/${id}`, params);

        const response = await fetch(url, {
            method: "DELETE",
            headers: { "Content-Type": "application/json" },
        });

        if (!response.ok) {
            const errText = await response.text();
            console.error("Backend DELETE error:", response.status, errText);
            return NextResponse.json(
                { success: false, error: "Backend delete failed" },
                { status: response.status }
            );
        }

        const result = await response.json();
        return NextResponse.json({
            success: true,
            message: "Event deleted",
            ...result,
        });
    } catch (error) {
        console.error("Calendar DELETE proxy error:", error);
        return NextResponse.json(
            { success: false, error: "Failed to delete event" },
            { status: 500 }
        );
    }
}
