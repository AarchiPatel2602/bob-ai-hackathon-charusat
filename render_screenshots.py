import os
from PIL import Image, ImageDraw, ImageFont

os.makedirs("demo/screenshots", exist_ok=True)

# Helper to get font or default
def get_fonts():
    try:
        f_title = ImageFont.truetype("arial.ttf", 26)
        f_subtitle = ImageFont.truetype("arial.ttf", 16)
        f_heading = ImageFont.truetype("arialbd.ttf", 18)
        f_body = ImageFont.truetype("arial.ttf", 14)
        f_bold = ImageFont.truetype("arialbd.ttf", 14)
        f_mono = ImageFont.truetype("consola.ttf", 13)
        f_small = ImageFont.truetype("arial.ttf", 11)
        f_badge = ImageFont.truetype("arialbd.ttf", 11)
    except Exception:
        f_title = f_subtitle = f_heading = f_body = f_bold = f_mono = f_small = f_badge = ImageFont.load_default()
    return f_title, f_subtitle, f_heading, f_body, f_bold, f_mono, f_small, f_badge

f_title, f_subtitle, f_heading, f_body, f_bold, f_mono, f_small, f_badge = get_fonts()

# Base Dark Mode Theme Colors
BG_DARK = (7, 11, 20)
NAV_BG = (13, 20, 36)
CARD_BG = (15, 23, 42)
BORDER_COL = (30, 41, 59)
TEXT_WHITE = (248, 250, 252)
TEXT_GRAY = (148, 163, 184)
ACCENT_BLUE = (56, 189, 248)
BLUE_BUTTON = (37, 99, 235)
RED_ALERT = (239, 68, 68)
AMBER_WARN = (245, 158, 11)
GREEN_OK = (34, 197, 94)

def draw_header_and_sidebar(draw, active_nav="dashboard"):
    # Left Sidebar
    draw.rectangle([0, 0, 240, 900], fill=NAV_BG)
    draw.line([240, 0, 240, 900], fill=BORDER_COL, width=1)
    
    # Sidebar Brand
    draw.rectangle([20, 20, 52, 52], fill=(30, 58, 138), outline=(59, 130, 246))
    draw.text((28, 26), "🚢", font=f_heading)
    draw.text((62, 22), "RouteWise", fill=TEXT_WHITE, font=f_heading)
    draw.text((156, 24), "AI", fill=ACCENT_BLUE, font=f_bold)
    draw.text((62, 44), "LOGISTICS COPILOT", fill=TEXT_GRAY, font=f_small)
    draw.line([0, 68, 240, 68], fill=BORDER_COL, width=1)

    # Sidebar Nav Items
    items = [
        ("dashboard", "📊 Dashboard"),
        ("copilot", "🤖 IBM Bob Copilot"),
        ("shipments", "📦 Shipments"),
        ("disruptions", "🚨 Disruptions"),
        ("alerts", "🔔 Alerts"),
        ("fleet", "🚛 Fleet Utilisation")
    ]
    y = 90
    for key, label in items:
        is_active = key == active_nav
        if is_active:
            draw.rectangle([12, y, 228, y + 36], fill=(30, 58, 138, 100), outline=(59, 130, 246), width=1)
            draw.text((24, y + 8), label, fill=TEXT_WHITE, font=f_bold)
        else:
            draw.text((24, y + 8), label, fill=TEXT_GRAY, font=f_body)
        y += 44

    # User footer in sidebar
    draw.line([0, 830, 240, 830], fill=BORDER_COL, width=1)
    draw.ellipse([20, 845, 52, 877], fill=(30, 41, 59), outline=(71, 85, 105))
    draw.text((31, 852), "A", fill=ACCENT_BLUE, font=f_bold)
    draw.text((62, 846), "Ayush Vyas", fill=TEXT_WHITE, font=f_bold)
    draw.text((62, 864), "CHARUSAT Innovators", fill=TEXT_GRAY, font=f_small)

    # Top Header Bar
    draw.rectangle([240, 0, 1440, 68], fill=(10, 16, 31))
    draw.line([240, 68, 1440, 68], fill=BORDER_COL, width=1)
    draw.text((265, 16), "RouteWise AI Control Tower", fill=TEXT_WHITE, font=f_heading)
    draw.text((265, 42), "Autonomous Disruption Correlation, Cold-Chain IoT Surveillance & Fleet Optimization", fill=TEXT_GRAY, font=f_small)

    # Header Telematics status pill
    draw.rectangle([980, 20, 1180, 48], fill=(6, 30, 25), outline=(5, 150, 105))
    draw.ellipse([995, 30, 1003, 38], fill=GREEN_OK)
    draw.text((1012, 27), "MCP Telematics Online", fill=GREEN_OK, font=f_badge)

    # Hero Demo Button
    draw.rectangle([1200, 18, 1410, 50], fill=BLUE_BUTTON, outline=(96, 165, 250))
    draw.text((1220, 26), "✨ Run Hackathon Demo", fill=TEXT_WHITE, font=f_bold)

# SCREENSHOT 1: Home Dashboard
def render_dashboard():
    img = Image.new("RGB", (1440, 900), BG_DARK)
    draw = ImageDraw.Draw(img)
    draw_header_and_sidebar(draw, "dashboard")

    # 4 KPI Summary Cards
    cards = [
        ("TOTAL ACTIVE SHIPMENTS", "53", "Global Fleet Corridors", ACCENT_BLUE),
        ("CONSIGNMENTS AT RISK", "1", "SH-1024 Vaccines Exposure", RED_ALERT),
        ("CARGO VALUE AT RISK", "$620,000", "Critical Consignment Exposure", RED_ALERT),
        ("FLEET UTILISATION", "68.8%", "TRUCK-205 Idle (Ahmedabad)", AMBER_WARN)
    ]
    cx = 265
    for title, val, sub, col in cards:
        draw.rectangle([cx, 85, cx + 270, 175], fill=CARD_BG, outline=BORDER_COL)
        draw.text((cx + 16, 98), title, fill=TEXT_GRAY, font=f_small)
        draw.text((cx + 16, 118), val, fill=col, font=f_title)
        draw.text((cx + 16, 152), sub, fill=TEXT_GRAY, font=f_small)
        cx += 290

    # Active Disruption Banner
    draw.rectangle([265, 190, 1410, 250], fill=(30, 15, 20), outline=RED_ALERT)
    draw.text((285, 202), "🚨 CRITICAL DISRUPTION DETECTED:", fill=RED_ALERT, font=f_bold)
    draw.text((540, 202), "Mumbai Port Strike — Port gate stoppage affecting Western India maritime lanes.", fill=TEXT_WHITE, font=f_body)
    draw.text((285, 226), "Affected High-Value Consignment: SH-1024 Vaccines ($620,000). Active risk elevated to 99/100 (CRITICAL).", fill=TEXT_GRAY, font=f_small)

    # Active Shipments Table (Left)
    draw.rectangle([265, 265, 960, 560], fill=CARD_BG, outline=BORDER_COL)
    draw.text((285, 280), "📦 High-Risk Consignments Requiring Decision Support", fill=TEXT_WHITE, font=f_heading)

    headers = ["ID", "Cargo", "Corridor", "Value", "Risk Score", "Severity"]
    hx = [285, 370, 480, 670, 770, 870]
    draw.line([285, 310, 940, 310], fill=BORDER_COL, width=1)
    for i, h in enumerate(headers):
        draw.text((hx[i], 318), h, fill=TEXT_GRAY, font=f_small)
    draw.line([285, 338, 940, 338], fill=BORDER_COL, width=1)

    shipments_data = [
        ("SH-1024", "Vaccines", "Mumbai ➔ Rotterdam", "$620,000", "99/100", "CRITICAL", RED_ALERT),
        ("SH-1035", "Perishables", "Singapore ➔ Hamburg", "$180,000", "72/100", "HIGH", AMBER_WARN),
        ("SH-1042", "Semiconductors", "Taipei ➔ Long Beach", "$450,000", "30/100", "LOW", GREEN_OK),
        ("SH-1055", "Biologics", "Mumbai ➔ Frankfurt", "$290,000", "28/100", "LOW", GREEN_OK),
        ("SH-1061", "Diagnostics", "Shanghai ➔ Antwerp", "$140,000", "22/100", "LOW", GREEN_OK)
    ]
    ry = 348
    for row in shipments_data:
        draw.text((hx[0], ry), row[0], fill=ACCENT_BLUE, font=f_bold)
        draw.text((hx[1], ry), row[1], fill=TEXT_WHITE, font=f_body)
        draw.text((hx[2], ry), row[2], fill=TEXT_WHITE, font=f_body)
        draw.text((hx[3], ry), row[3], fill=TEXT_WHITE, font=f_body)
        draw.text((hx[4], ry), row[4], fill=row[6], font=f_bold)
        draw.rectangle([hx[5], ry - 2, hx[5] + 65, ry + 18], fill=CARD_BG, outline=row[6])
        draw.text((hx[5] + 6, ry + 1), row[5], fill=row[6], font=f_badge)
        ry += 38
        draw.line([285, ry - 8, 940, ry - 8], fill=(20, 27, 45), width=1)

    # Cold-Chain Telemetry Panel (Right)
    draw.rectangle([980, 265, 1410, 560], fill=CARD_BG, outline=BORDER_COL)
    draw.text((1000, 280), "❄️ Cold-Chain IoT (SH-1024)", fill=TEXT_WHITE, font=f_heading)
    draw.text((1000, 305), "Pharma Profile: 2.0°C – 8.0°C | Sensor #SENS-8841", fill=TEXT_GRAY, font=f_small)

    # Draw simulated temperature graph
    draw.rectangle([1000, 330, 1390, 480], fill=(10, 15, 28), outline=BORDER_COL)
    draw.line([1000, 360, 1390, 360], fill=RED_ALERT, width=1) # Upper threshold 8°C
    draw.text((1010, 345), "Upper Threshold (8.0°C)", fill=RED_ALERT, font=f_small)
    draw.line([1000, 450, 1390, 450], fill=BLUE_BUTTON, width=1) # Lower threshold 2°C
    draw.text((1010, 455), "Lower Threshold (2.0°C)", fill=ACCENT_BLUE, font=f_small)

    # Curve points
    pts = [(1020, 410), (1080, 395), (1140, 380), (1200, 350), (1260, 320), (1340, 300)]
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i+1]], fill=AMBER_WARN, width=3)
    draw.ellipse([pts[-1][0]-4, pts[-1][1]-4, pts[-1][0]+4, pts[-1][1]+4], fill=RED_ALERT)
    draw.text((pts[-1][0]-30, pts[-1][1]-20), "8.4°C BREACH", fill=RED_ALERT, font=f_bold)

    draw.rectangle([1000, 495, 1390, 545], fill=(30, 15, 20), outline=RED_ALERT)
    draw.text((1010, 503), "PREDICTIVE BREACH ALERT: Thermal slope ΔT/Δt = +0.38°C/h", fill=RED_ALERT, font=f_bold)
    draw.text((1010, 523), "Immediate reroute & auxiliary power verification recommended.", fill=TEXT_GRAY, font=f_small)

    # Bottom Row: Multimodal Rerouting & Fleet
    draw.rectangle([265, 580, 830, 870], fill=CARD_BG, outline=BORDER_COL)
    draw.text((285, 595), "🗺️ Multimodal Rerouting What-If Analysis (SH-1024)", fill=TEXT_WHITE, font=f_heading)
    draw.text((285, 622), "Original Corridor: Mumbai ➔ Rotterdam (Risk 99/100 CRITICAL)", fill=TEXT_GRAY, font=f_small)

    routes = [
        ("Alternative A: Colombo Maritime Transshipment", "Ocean Bypass", "+18h", "+$8,400", "24/100 (LOW)", "RECOMMENDED", GREEN_OK),
        ("Alternative C: Intermodal Air-Sea via Frankfurt", "Air Diversion", "+6h", "+$18,500", "12/100 (LOW)", "FASTEST", ACCENT_BLUE),
        ("Alternative B: Cape Route via Singapore", "Ocean Lane", "+32h", "+$5,200", "42/100 (MED)", "BEST VALUE", TEXT_GRAY)
    ]
    ry = 650
    for r in routes:
        draw.rectangle([285, ry, 810, ry + 60], fill=(18, 28, 48), outline=BORDER_COL)
        draw.text((295, ry + 8), r[0], fill=TEXT_WHITE, font=f_bold)
        draw.text((295, ry + 32), f"Mode: {r[1]} | Time: {r[2]} | Cost: {r[3]} | Projected Risk: {r[4]}", fill=TEXT_GRAY, font=f_small)
        draw.rectangle([710, ry + 12, 795, ry + 36], fill=CARD_BG, outline=r[6])
        draw.text((718, ry + 17), r[5], fill=r[6], font=f_badge)
        ry += 70

    draw.rectangle([850, 580, 1410, 870], fill=CARD_BG, outline=BORDER_COL)
    draw.text((870, 595), "🚛 Fleet Utilisation & Idle Asset Repositioning", fill=TEXT_WHITE, font=f_heading)
    draw.text((870, 622), "Network Utilisation: 68.8% | 14 Active Assets | 2 Idle Assets", fill=TEXT_GRAY, font=f_small)

    draw.rectangle([870, 650, 1390, 750], fill=(18, 28, 48), outline=(59, 130, 246))
    draw.text((885, 662), "TRUCK-205 (10 Tons Refrigerated Reefer)", fill=TEXT_WHITE, font=f_bold)
    draw.text((885, 686), "Current Location: Ahmedabad (Idle for 8.0 hours) | Dwell Threshold: Exceeded", fill=TEXT_GRAY, font=f_small)
    draw.text((885, 712), "Autonomous Recommendation: Reposition to Mumbai port buffer corridor.", fill=ACCENT_BLUE, font=f_body)

    draw.rectangle([870, 770, 1390, 845], fill=CARD_BG, outline=GREEN_OK)
    draw.text((885, 782), "Projected Utilisation Gain: +3.4% Network Recovery", fill=GREEN_OK, font=f_bold)
    draw.text((885, 808), "Relieves vaccine storage bottleneck caused by Mumbai port strike.", fill=TEXT_GRAY, font=f_small)

    img.save("demo/screenshots/01-home-dashboard.png")
    print("[SAVED] demo/screenshots/01-home-dashboard.png")

# SCREENSHOT 2: IBM Bob Query Input
def render_query_input():
    img = Image.new("RGB", (1440, 900), BG_DARK)
    draw = ImageDraw.Draw(img)
    draw_header_and_sidebar(draw, "copilot")

    # Copilot Header
    draw.rectangle([265, 85, 1410, 150], fill=CARD_BG, outline=BORDER_COL)
    draw.ellipse([285, 98, 325, 138], fill=(30, 58, 138), outline=ACCENT_BLUE)
    draw.text((298, 107), "🤖", font=f_heading)
    draw.text((340, 98), "IBM Bob Copilot — Conversational Supply Chain Assistant", fill=TEXT_WHITE, font=f_heading)
    draw.text((340, 124), "Connected to RouteWise Model Context Protocol (MCP) Tools & IBM watsonx / Granite", fill=TEXT_GRAY, font=f_small)

    # Chat Canvas Area
    draw.rectangle([265, 165, 1410, 740], fill=(10, 16, 31), outline=BORDER_COL)

    # Welcome Message from Bob
    draw.rectangle([290, 185, 1050, 290], fill=CARD_BG, outline=BORDER_COL)
    draw.text((305, 198), "🤖 IBM Bob", fill=ACCENT_BLUE, font=f_bold)
    draw.text((305, 222), "Hello! I am IBM Bob, your intelligent logistics copilot powered by RouteWise AI.", fill=TEXT_WHITE, font=f_body)
    draw.text((305, 244), "I continuously monitor active transit corridors, cold-chain IoT sensors, and fleet availability.", fill=TEXT_WHITE, font=f_body)
    draw.text((305, 266), "Ask me about current disruption bottlenecks, high-risk consignments, or recommended bypass corridors.", fill=TEXT_GRAY, font=f_small)

    # Suggested Prompts Chips
    draw.text((290, 315), "Suggested Prompts:", fill=TEXT_GRAY, font=f_bold)
    chips = [
        "Which shipments are currently at risk?",
        "Which shipment is most urgent?",
        "Why is shipment SH-1024 at risk?",
        "Which fleet assets are currently idle?"
    ]
    cx = 290
    for chip in chips:
        draw.rectangle([cx, 340, cx + len(chip)*8 + 20, 372], fill=(20, 30, 55), outline=BORDER_COL)
        draw.text((cx + 10, 348), chip, fill=ACCENT_BLUE, font=f_small)
        cx += len(chip)*8 + 32

    # User Query Active Input
    draw.rectangle([650, 410, 1380, 480], fill=(37, 99, 235), outline=(96, 165, 250))
    draw.text((670, 424), "Which shipments are currently at risk?", fill=TEXT_WHITE, font=f_heading)
    draw.text((670, 452), "Sent by Ayush Vyas • 11:24 AM", fill=(219, 234, 254), font=f_small)

    # Typing / Processing Indicator
    draw.rectangle([290, 510, 720, 560], fill=CARD_BG, outline=BORDER_COL)
    draw.text((305, 526), "⚡ Querying MCP Tool get_active_shipments & reasoning...", fill=AMBER_WARN, font=f_body)

    # Input Bar at Bottom
    draw.rectangle([265, 760, 1410, 860], fill=CARD_BG, outline=BORDER_COL)
    draw.rectangle([285, 780, 1260, 840], fill=(10, 16, 31), outline=(59, 130, 246))
    draw.text((305, 798), "Which shipments are currently at risk?|", fill=TEXT_WHITE, font=f_body)

    draw.rectangle([1280, 780, 1390, 840], fill=BLUE_BUTTON, outline=(96, 165, 250))
    draw.text((1315, 800), "Send ➔", fill=TEXT_WHITE, font=f_bold)

    img.save("demo/screenshots/02-query-input.png")
    print("[SAVED] demo/screenshots/02-query-input.png")

# SCREENSHOT 3: Result Output
def render_result_output():
    img = Image.new("RGB", (1440, 900), BG_DARK)
    draw = ImageDraw.Draw(img)
    draw_header_and_sidebar(draw, "copilot")

    # Copilot Header
    draw.rectangle([265, 85, 1410, 150], fill=CARD_BG, outline=BORDER_COL)
    draw.ellipse([285, 98, 325, 138], fill=(30, 58, 138), outline=ACCENT_BLUE)
    draw.text((298, 107), "🤖", font=f_heading)
    draw.text((340, 98), "IBM Bob Copilot — Conversational Supply Chain Assistant", fill=TEXT_WHITE, font=f_heading)
    draw.text((340, 124), "Reasoning Source: IBM WatsonX / Bob Assistant & RouteWise Deterministic Engine", fill=GREEN_OK, font=f_small)

    # Chat Messages Area
    draw.rectangle([265, 165, 1410, 870], fill=(10, 16, 31), outline=BORDER_COL)

    # User Query
    draw.rectangle([700, 185, 1380, 245], fill=BLUE_BUTTON, outline=(96, 165, 250))
    draw.text((720, 200), "Why is shipment SH-1024 at risk and what should we do?", fill=TEXT_WHITE, font=f_heading)
    draw.text((720, 226), "Sent by Logistics Director • 11:25 AM", fill=(219, 234, 254), font=f_small)

    # Bob's Structured Response Box
    draw.rectangle([290, 265, 1380, 750], fill=CARD_BG, outline=BORDER_COL)
    draw.text((315, 285), "🤖 IBM Bob's Root-Cause Analysis & Decision Support", fill=ACCENT_BLUE, font=f_heading)

    # Severity Banner inside response
    draw.rectangle([315, 320, 1355, 365], fill=(40, 15, 20), outline=RED_ALERT)
    draw.text((330, 332), "SEVERITY: CRITICAL", fill=RED_ALERT, font=f_bold)
    draw.text((500, 332), "Risk Score: 99/100 | Cargo: Vaccines ($620,000) | Corridor: Mumbai ➔ Rotterdam", fill=TEXT_WHITE, font=f_body)

    # Section 1: Finding
    draw.text((315, 385), "1. Operational Finding:", fill=TEXT_WHITE, font=f_bold)
    draw.text((315, 408), "Shipment SH-1024 is exposed to compounding failure modes: origin corridor blockage + cold-chain thermal anomaly.", fill=TEXT_GRAY, font=f_body)

    # Section 2: Ground-truth Evidence from MCP
    draw.text((315, 440), "2. Ground-Truth Evidence (Retrieved via MCP):", fill=TEXT_WHITE, font=f_bold)
    draw.text((330, 462), "• Corridor Disruption: Mumbai Port Strike (High Severity, expected 4 days closure). Gate operations halted.", fill=TEXT_GRAY, font=f_body)
    draw.text((330, 484), "• Cold-Chain Breach: Telemetry indicates rise from 7.8°C to 8.4°C (Upper threshold: 8.0°C).", fill=TEXT_GRAY, font=f_body)
    draw.text((330, 506), "• Predictive Slope: Thermal velocity +0.38°C/hr indicates irreversible biological degradation within 3 hours.", fill=RED_ALERT, font=f_body)

    # Section 3: Recommended Action Plan
    draw.rectangle([315, 540, 1355, 640], fill=(15, 35, 25), outline=GREEN_OK)
    draw.text((330, 552), "3. Autonomous Recommendation & Action Plan:", fill=GREEN_OK, font=f_heading)
    draw.text((330, 580), "• Reroute: Approve Alternative A (Transshipment via Colombo Maritime Hub). Adds +18h and +$8,400.", fill=TEXT_WHITE, font=f_body)
    draw.text((330, 602), "• Risk Impact: Projected risk plummets from 99/100 down to 24/100 (LOW), protecting $620,000 consignment.", fill=TEXT_WHITE, font=f_body)

    # 1-Click Action Buttons
    draw.rectangle([315, 660, 520, 710], fill=GREEN_OK, outline=(134, 239, 172))
    draw.text((345, 676), "✓ Approve Colombo Reroute", fill=(10, 40, 20), font=f_bold)

    draw.rectangle([540, 660, 770, 710], fill=BLUE_BUTTON, outline=(96, 165, 250))
    draw.text((565, 676), "🚛 Dispatch TRUCK-205 (Reefer)", fill=TEXT_WHITE, font=f_bold)

    draw.rectangle([790, 660, 960, 710], fill=CARD_BG, outline=BORDER_COL)
    draw.text((820, 676), "Inspect IoT Telemetry", fill=TEXT_GRAY, font=f_body)

    # Footer note
    draw.text((315, 725), "Provider: IBM WatsonX / Bob Assistant & RouteWise AI Deterministic Engine | Confidence: 99.4%", fill=TEXT_GRAY, font=f_small)

    img.save("demo/screenshots/03-result-output.png")
    print("[SAVED] demo/screenshots/03-result-output.png")

if __name__ == "__main__":
    render_dashboard()
    render_query_input()
    render_result_output()
