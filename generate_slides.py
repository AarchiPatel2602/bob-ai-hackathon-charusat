import os
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        # Top line
        self.setStrokeColor(colors.HexColor("#1e293b"))
        self.setLineWidth(0.5)
        self.line(40, 35, 752, 35)
        # Footer text
        self.drawString(40, 22, "RouteWise AI | IBM Bob AI Hackathon 2026 | CHARUSAT Innovators")
        self.drawRightString(752, 22, f"Slide {self._pageNumber} of {page_count}")
        self.restoreState()

def build_pdf():
    os.makedirs("presentation", exist_ok=True)
    pdf_path = os.path.join("presentation", "slides.pdf")
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=landscape(letter),
        leftMargin=45,
        rightMargin=45,
        topMargin=40,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    # Custom color palette
    c_bg = colors.HexColor("#0f172a")
    c_primary = colors.HexColor("#38bdf8")
    c_accent = colors.HexColor("#6366f1")
    c_text = colors.HexColor("#f8fafc")
    c_sub = colors.HexColor("#94a3b8")
    c_card = colors.HexColor("#1e293b")

    # Typography styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=32,
        leading=38,
        textColor=colors.HexColor("#0f172a"),
        alignment=0
    )
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=15,
        leading=20,
        textColor=colors.HexColor("#334155"),
        alignment=0
    )
    slide_title_style = ParagraphStyle(
        'SlideTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=12
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1e40af"),
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155")
    )
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
        leftIndent=12,
        spaceAfter=4
    )
    card_title = ParagraphStyle(
        'CardTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#0f172a")
    )
    card_text = ParagraphStyle(
        'CardText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569")
    )

    story = []

    # -------------------------------------------------------------
    # SLIDE 1: Title Slide
    # -------------------------------------------------------------
    story.append(Spacer(1, 40))
    story.append(Paragraph("RouteWise AI 🚢", title_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Intelligent Supply-Chain Disruption Copilot & Fleet Resilience Control Tower", subtitle_style))
    story.append(Spacer(1, 24))

    meta_table = [
        [Paragraph("<b>Track:</b> AI", body_style), Paragraph("<b>Event:</b> IBM Bob AI Innovation Hackathon 2026", body_style)],
        [Paragraph("<b>Team:</b> CHARUSAT Innovators", body_style), Paragraph("<b>Lead:</b> Ayush Vyas (D25IT130@CHARUSAT.EDU.IN)", body_style)],
        [Paragraph("<b>Members:</b> Aarchi Patel, Nitya Chokshi, Hitarth Chauhan", body_style), Paragraph("<b>Repository:</b> github.com/AarchiPatel2602/bob-ai-hackathon-charusat", body_style)]
    ]
    t1 = Table(meta_table, colWidths=[340, 360])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t1)
    story.append(PageBreak())

    # -------------------------------------------------------------
    # SLIDE 2: The Problem
    # -------------------------------------------------------------
    story.append(Paragraph("The Challenge: Fragmented Visibility & Cold-Chain Fragility", slide_title_style))
    story.append(Paragraph("Global supply chains suffer from severe information silos during unforeseen operational shocks:", body_style))
    story.append(Spacer(1, 10))

    cards_s2 = [
        [
            Paragraph("<b>Fragmented Disruption Telemetry</b>", card_title),
            Paragraph("<b>Compounding Cold-Chain Risks</b>", card_title),
            Paragraph("<b>Manual Decision Latency</b>", card_title)
        ],
        [
            Paragraph("Weather anomalies, port strikes, and canal blockages are reported across disconnected web feeds. Dispatchers lack unified spatial correlation to determine which shipments are directly impacted.", card_text),
            Paragraph("High-value pharmaceuticals (vaccines, biologics) require strict 2°C–8°C compliance. Unnoticed transit bottlenecks cause container battery drains and catastrophic cargo spoilage.", card_text),
            Paragraph("Evaluating alternative transshipment corridors, carrier reliability, freight surcharges, and fleet availability takes hours of manual spreadsheet reconciliation.", card_text)
        ]
    ]
    t2 = Table(cards_s2, colWidths=[230, 230, 230])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('PADDING', (0,0), (-1,-1), 10),
        ('LINEBELOW', (0,0), (-1,0), 1, colors.HexColor("#3b82f6")),
    ]))
    story.append(t2)
    story.append(Spacer(1, 16))
    story.append(Paragraph("<b>Operational Impact:</b> Millions in cargo value exposed, regulatory compliance breaches, and low fleet utilisation during critical disruption spikes.", body_style))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # SLIDE 3: Solution Overview
    # -------------------------------------------------------------
    story.append(Paragraph("The Solution: RouteWise AI Intelligent Control Tower", slide_title_style))
    story.append(Paragraph("RouteWise AI connects every stage of the logistics decision loop into an autonomous, proactive workflow:", body_style))
    story.append(Spacer(1, 10))

    chain_data = [
        [Paragraph("<b>DISRUPTION</b>", card_title), Paragraph("<b>➔</b>", card_title), Paragraph("<b>IMPACT & RISK</b>", card_title), Paragraph("<b>➔</b>", card_title), Paragraph("<b>ALTERNATIVES</b>", card_title), Paragraph("<b>➔</b>", card_title), Paragraph("<b>DECISION & FLEET</b>", card_title)],
        [
            Paragraph("Port strikes, storms & route closures detected via MCP connectors", card_text),
            Paragraph("", card_text),
            Paragraph("Deterministic 0–100 risk scoring and thermal slope excursion forecast", card_text),
            Paragraph("", card_text),
            Paragraph("Ranked bypass corridors (time, cost & cold-chain verified)", card_text),
            Paragraph("", card_text),
            Paragraph("Idle fleet redeployment + 1-click execution & audit logging", card_text)
        ]
    ]
    t3 = Table(chain_data, colWidths=[150, 20, 150, 20, 160, 20, 170])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f0fdf4")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#bbf7d0")),
        ('ALIGN', (1,0), (1,-1), 'CENTER'),
        ('ALIGN', (3,0), (3,-1), 'CENTER'),
        ('ALIGN', (5,0), (5,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t3)
    story.append(Spacer(1, 14))
    story.append(Paragraph("<b>Key Breakthroughs:</b>", section_heading))
    story.append(Paragraph("• <b>Deterministic Zero-Hallucination Risk Engine:</b> Standardized 0–100 scoring with human-auditable risk drivers.", bullet_style))
    story.append(Paragraph("• <b>Predictive Thermal Slope:</b> Alerts dispatchers <i>before</i> upper thresholds (8.0°C) are breached.", bullet_style))
    story.append(Paragraph("• <b>Conversational IBM Bob Copilot:</b> Natural language dialogue with full contextual database grounding.", bullet_style))
    story.append(PageBreak())

    # -------------------------------------------------------------
    # SLIDE 4: Architecture
    # -------------------------------------------------------------
    story.append(Paragraph("Technical Architecture: Multi-Tier Resilient System", slide_title_style))
    story.append(Spacer(1, 5))

    arch_data = [
        [Paragraph("<b>Layer</b>", card_title), Paragraph("<b>Technologies</b>", card_title), Paragraph("<b>Role & Responsibilities</b>", card_title)],
        [Paragraph("<b>Frontend Control Tower</b>", body_style), Paragraph("React 19, TypeScript, Vite, Tailwind v4, Leaflet", body_style), Paragraph("Interactive live map, IoT temperature simulator, 1-click approval modal, IBM Bob conversational copilot drawer.", body_style)],
        [Paragraph("<b>Companion Dashboard</b>", body_style), Paragraph("Streamlit, Pandas, Python 3.13", body_style), Paragraph("Lightweight demonstration companion dashboard for instant single-command evaluation.", body_style)],
        [Paragraph("<b>Backend Gateway</b>", body_style), Paragraph("FastAPI, SQLAlchemy 2.0, Pydantic v2, SQLite / MySQL", body_style), Paragraph("High-speed asynchronous REST API, JWT authentication, CORS security, transaction management.", body_style)],
        [Paragraph("<b>10 Decision Engines</b>", body_style), Paragraph("Python Math, Spatial Correlators, Slope Analyzers", body_style), Paragraph("Disruption, Risk (0-100), Alternative Route, Carrier Ranking, Fleet Utilisation, Cold-Chain IoT, Alert & Audit.", body_style)],
        [Paragraph("<b>MCP Protocol Server</b>", body_style), Paragraph("JSON-RPC 2.0, Model Context Protocol Schema", body_style), Paragraph("Standardized AI tool integration: exposes active shipments, disruptions, route evaluation, and idle fleet queries.", body_style)],
        [Paragraph("<b>AI / IBM Bob Layer</b>", body_style), Paragraph("IBM WatsonX / Bob API + Deterministic Fallback", body_style), Paragraph("Natural language synthesis with strict factual grounding. Operates 100% offline if credentials are omitted.", body_style)]
    ]
    t4 = Table(arch_data, colWidths=[150, 190, 360])
    t4.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#94a3b8")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t4)
    story.append(PageBreak())

    # -------------------------------------------------------------
    # SLIDE 5: Key Engines
    # -------------------------------------------------------------
    story.append(Paragraph("Core Calculation & Surveillance Engines", slide_title_style))
    story.append(Spacer(1, 5))

    eng_data = [
        [
            Paragraph("<b>1. Cold-Chain IoT Engine</b>", card_title),
            Paragraph("<b>2. Deterministic Risk Engine</b>", card_title)
        ],
        [
            Paragraph("• Configurable compliance profiles (e.g. Pharma 2°C–8°C)<br/>• Severity classification: NORMAL, WARNING, MAJOR, CRITICAL<br/>• Predictive thermal slope: calculates rate of change ΔT/Δt to forecast breach time before cargo is damaged.", card_text),
            Paragraph("• Standardized 0–100 scoring (Low, Medium, High, Critical)<br/>• Factors disruption proximity, delay hours, cargo value exposure, priority class, and active thermal excursions.", card_text)
        ],
        [
            Paragraph("<b>3. Multimodal Reroute Engine</b>", card_title),
            Paragraph("<b>4. Fleet Utilisation Engine</b>", card_title)
        ],
        [
            Paragraph("• Auto-generates bypass transshipment corridors<br/>• Evaluates delta transit hours, freight surcharges, and projected risk drop (e.g. 99/100 ➔ 24/100 via Colombo)<br/>• Evaluates carrier performance & reefer certifications.", card_text),
            Paragraph("• Calculates exact network utilisation (Active vs Total Capacity)<br/>• Dwell-time monitoring: detects idle assets (e.g. TRUCK-205 in Ahmedabad idle 8h)<br/>• Recommends repositioning to surge bottleneck corridors.", card_text)
        ]
    ]
    t5 = Table(eng_data, colWidths=[350, 350])
    t5.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t5)
    story.append(PageBreak())

    # -------------------------------------------------------------
    # SLIDE 6: IBM Technologies Integration
    # -------------------------------------------------------------
    story.append(Paragraph("IBM Technology Stack & Bob Copilot Integration", slide_title_style))
    story.append(Paragraph("RouteWise AI incorporates IBM core technologies across the intelligence pipeline:", body_style))
    story.append(Spacer(1, 8))

    ibm_data = [
        [Paragraph("<b>Technology</b>", card_title), Paragraph("<b>Implementation Architecture</b>", card_title), Paragraph("<b>Operational Benefit</b>", card_title)],
        [
            Paragraph("<b>IBM Bob Conversational Copilot</b>", body_style),
            Paragraph("Dedicated conversational drawer and REST endpoint (/api/ai/chat) powered by supply-chain intent routing.", body_style),
            Paragraph("Logistics managers query network health naturally ('Which shipments are most urgent?', 'Should SH-1024 be rerouted?') with instant evidence.", body_style)
        ],
        [
            Paragraph("<b>IBM watsonx.ai / Granite</b>", body_style),
            Paragraph("Targeted prompt engineering with strict operational grounding context and hyperparameter tuning.", body_style),
            Paragraph("Synthesizes clear situation overviews, risk rationale, and tradeoff comparisons without fabricating external data.", body_style)
        ],
        [
            Paragraph("<b>Model Context Protocol (MCP)</b>", body_style),
            Paragraph("Standardized tool registry exposing 6 core logistics functions via JSON-RPC stdio and REST.", body_style),
            Paragraph("Enables external AI agents, IDE assistants, and enterprise systems to query telemetry, disruptions, and rerouting tools.", body_style)
        ],
        [
            Paragraph("<b>Graceful Offline Fallback</b>", body_style),
            Paragraph("Deterministic local decision support engine activates if IBM credentials are unconfigured.", body_style),
            Paragraph("Guarantees 100% operational uptime for mission-critical supply chains during air-gapped or offline scenarios.", body_style)
        ]
    ]
    t6 = Table(ibm_data, colWidths=[160, 260, 280])
    t6.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e0e7ff")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#818cf8")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#c7d2fe")),
        ('PADDING', (0,0), (-1,-1), 7),
    ]))
    story.append(t6)
    story.append(PageBreak())

    # -------------------------------------------------------------
    # SLIDE 7: Verification & Demonstration Scenario
    # -------------------------------------------------------------
    story.append(Paragraph("Verification & 1-Click Hackathon Demonstration Flow", slide_title_style))
    story.append(Spacer(1, 5))

    verif_text = """
    <b>Demonstrated End-to-End Scenario:</b><br/>
    1. <b>Baseline State:</b> 53 active shipments, 3 disruptions, 68.8% fleet utilisation.<br/>
    2. <b>Disruption Event:</b> Mumbai Port Strike (High Severity, 4-day closure). SH-1024 (Vaccines, $620,000, Mumbai ➔ Rotterdam) origin is blocked.<br/>
    3. <b>IoT Excursion:</b> Simulated thermal rise (7.8°C ➔ 8.4°C). Predictive slope alerts imminent breach of upper 8.0°C compliance bound. Risk spikes to <b>99/100 (CRITICAL)</b>.<br/>
    4. <b>Autonomous Recommendation:</b> Reroute via <i>Alternative A (Colombo Transshipment Hub)</i> (+18h, +$8,400, risk drops to 24) and redeploy idle <i>TRUCK-205</i> from Ahmedabad to relieve backlog.<br/>
    5. <b>1-Click Action & Audit:</b> Manager approves reroute; decision recorded in immutable audit log; fleet utilisation rises to 72.2%.
    """
    story.append(Paragraph(verif_text, body_style))
    story.append(Spacer(1, 10))

    test_box = [
        [Paragraph("<b>Automated Test Suite Status</b>", card_title), Paragraph("<b>Result</b>", card_title)],
        [Paragraph("Pytest Backend Unit Test Suite (19 test cases)", body_style), Paragraph("<font color='#16a34a'><b>19 / 19 PASSED (100%)</b></font>", body_style)],
        [Paragraph("Live End-to-End API Integration Suite (15 test workflows)", body_style), Paragraph("<font color='#16a34a'><b>15 / 15 PASSED (100%)</b></font>", body_style)],
        [Paragraph("Model Context Protocol (MCP) Tool Verification", body_style), Paragraph("<font color='#16a34a'><b>6 / 6 TOOLS VERIFIED</b></font>", body_style)],
        [Paragraph("React 19 + TypeScript + Vite Frontend Build", body_style), Paragraph("<font color='#16a34a'><b>0 ERRORS (618ms Build)</b></font>", body_style)]
    ]
    t7 = Table(test_box, colWidths=[480, 220])
    t7.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f0fdf4")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#86efac")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#bbf7d0")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t7)
    story.append(PageBreak())

    # -------------------------------------------------------------
    # SLIDE 8: Team & Vision
    # -------------------------------------------------------------
    story.append(Paragraph("Team CHARUSAT Innovators & Future Roadmap", slide_title_style))
    story.append(Spacer(1, 5))

    team_data = [
        [
            Paragraph("<b>Ayush Vyas</b><br/><font size=8 color='#64748b'>Team Lead & Full-Stack Architect</font><br/><font size=7 color='#0284c7'>D25IT130@CHARUSAT.EDU.IN</font>", body_style),
            Paragraph("<b>Aarchi Patel</b><br/><font size=8 color='#64748b'>AI & Frontend Engineer</font><br/><font size=7 color='#0284c7'>D25IT133@charusat.edu.in</font>", body_style),
            Paragraph("<b>Nitya Chokshi</b><br/><font size=8 color='#64748b'>Data & Operations Engineer</font><br/><font size=7 color='#0284c7'>D25ME097@charusat.edu.in</font>", body_style),
            Paragraph("<b>Hitarth Chauhan</b><br/><font size=8 color='#64748b'>Systems & QA Engineer</font><br/><font size=7 color='#0284c7'>24ME006@charusat.edu.in</font>", body_style)
        ]
    ]
    t8 = Table(team_data, colWidths=[175, 175, 175, 175])
    t8.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t8)
    story.append(Spacer(1, 14))

    story.append(Paragraph("<b>Future Development Roadmap:</b>", section_heading))
    story.append(Paragraph("• <b>Live Telematics Ingestion:</b> Connect real-time GPS & OBD-II telemetry streams via MQTT/Kafka.", bullet_style))
    story.append(Paragraph("• <b>Autonomous Carrier Bidding:</b> Multi-agent negotiation protocol for automated spot rate booking during emergency reroutes.", bullet_style))
    story.append(Paragraph("• <b>Predictive Micro-Climate Modeling:</b> Ingest NOAA and ECMWF global weather forecast grids into spatial risk matrices.", bullet_style))
    story.append(Paragraph("• <b>Enterprise ERP Bridges:</b> Turnkey bi-directional integrations with SAP Transportation Management and Oracle SCM Cloud.", bullet_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] Generated presentation slides at: {pdf_path}")

if __name__ == "__main__":
    build_pdf()
