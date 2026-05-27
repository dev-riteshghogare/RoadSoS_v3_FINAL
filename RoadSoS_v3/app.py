import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from modules.database import (init_db, get_nearby_services, get_nearest_trauma_center,
                               get_emergency_numbers, log_incident, get_analytics)
from modules.ai_assistant import (analyze_severity, get_golden_hour_analysis,
                                   translate_emergency, generate_first_aid_steps, chat_response)
from modules.utils import *
from modules.voice_sos import get_voice_component_html
from modules.live_map import build_emergency_map, get_gps_html
from modules.sms_alert import (build_emergency_sms, send_sms_twilio,
                                 get_whatsapp_link, get_sms_link, send_bulk_alerts)

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RoadSoS – AI Emergency Assistant",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;600&display=swap');
*, html, body { font-family: 'DM Sans', sans-serif; }

.hero {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    padding: 2rem 2.5rem; border-radius: 20px; color: white;
    margin-bottom: 1.5rem; position: relative; overflow: hidden;
}
.hero::before {
    content:''; position:absolute; top:-50%; left:-50%;
    width:200%; height:200%;
    background: radial-gradient(circle, rgba(231,76,60,0.15) 0%, transparent 60%);
    animation: pulse-bg 3s ease-in-out infinite;
}
@keyframes pulse-bg { 0%,100%{transform:scale(1)} 50%{transform:scale(1.1)} }
.hero h1 { font-family:'Syne',sans-serif; font-size:2.8rem; font-weight:800; margin:0; letter-spacing:-2px; }
.hero p { opacity:0.8; margin:0.3rem 0 0.8rem 0; font-size:1rem; }
.badge { background:rgba(231,76,60,0.3); border:1px solid rgba(231,76,60,0.5); color:#ff6b6b; padding:3px 12px; border-radius:20px; font-size:0.75rem; font-weight:600; margin-right:6px; display:inline-block; }
.badge-green { background:rgba(39,174,96,0.3); border:1px solid rgba(39,174,96,0.5); color:#2ecc71; padding:3px 12px; border-radius:20px; font-size:0.75rem; font-weight:600; margin-right:6px; display:inline-block; }

.severity-card { border-radius:14px; padding:1.2rem 1.5rem; margin:0.8rem 0; color:white; position:relative; }
.severity-score { position:absolute; top:1rem; right:1rem; font-family:'Syne',sans-serif; font-size:2rem; font-weight:800; opacity:0.3; }

.service-card { background:white; border-radius:12px; padding:1rem 1.2rem; margin:0.5rem 0; border-left:4px solid #e74c3c; box-shadow:0 2px 10px rgba(0,0,0,0.06); transition:all 0.2s; }
.service-card:hover { transform:translateX(4px); }
.service-card h4 { margin:0 0 0.2rem 0; font-size:0.9rem; font-weight:600; color:#1a1a2e; }
.service-card p { margin:0; font-size:0.78rem; color:#666; }
.dist-tag { background:#e74c3c; color:white; padding:2px 8px; border-radius:20px; font-size:0.7rem; font-weight:600; float:right; }
.eta-tag { background:#2c3e50; color:white; padding:2px 8px; border-radius:20px; font-size:0.7rem; float:right; margin-right:4px; }

.golden-box { background:linear-gradient(135deg,#f39c12,#e67e22); color:white; border-radius:14px; padding:1.2rem 1.5rem; margin:1rem 0; }
.golden-box h3 { margin:0 0 0.5rem 0; font-family:'Syne',sans-serif; font-size:1.1rem; }

.chat-user { background:linear-gradient(135deg,#e74c3c,#c0392b); color:white; padding:0.8rem 1.1rem; border-radius:16px 16px 4px 16px; margin:0.4rem 0 0.4rem auto; max-width:78%; font-size:0.9rem; line-height:1.5; }
.chat-bot { background:#f1f3f5; color:#1a1a2e; padding:0.8rem 1.1rem; border-radius:16px 16px 16px 4px; margin:0.4rem auto 0.4rem 0; max-width:82%; font-size:0.9rem; line-height:1.5; border:1px solid #e9ecef; }

.stat-pill { background:#1a1a2e; color:white; border-radius:12px; padding:1rem; text-align:center; }
.stat-pill .num { font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800; color:#e74c3c; display:block; }
.stat-pill .lbl { font-size:0.7rem; opacity:0.6; text-transform:uppercase; letter-spacing:0.5px; }

.action-step { display:flex; align-items:flex-start; gap:0.8rem; background:#fff5f5; border-radius:10px; padding:0.7rem 1rem; margin:0.3rem 0; border:1px solid #fde8e8; }
.step-circle { width:26px; height:26px; border-radius:50%; background:#e74c3c; color:white; display:flex; align-items:center; justify-content:center; font-size:0.75rem; font-weight:700; flex-shrink:0; }

.sms-card { background:linear-gradient(135deg,#1a1a2e,#0d3349); color:white; border-radius:14px; padding:1.2rem; margin:0.5rem 0; border:1px solid rgba(39,174,96,0.3); }
.sms-card h4 { margin:0 0 0.4rem 0; font-family:'Syne',sans-serif; font-size:1rem; }

.crash-alert { background:linear-gradient(135deg,#c0392b,#922b21); color:white; border-radius:14px; padding:1rem 1.5rem; margin:0.5rem 0; animation:flash 1s ease-in-out 4; }
@keyframes flash { 0%,100%{opacity:1} 50%{opacity:0.6} }
</style>
""", unsafe_allow_html=True)

# ─── Init ─────────────────────────────────────────────────────────────────────
init_db()
for k, v in {
    "messages": [], "severity_result": None, "golden_hour": None,
    "golden_trauma": None, "first_aid_steps": [], "translated_text": "",
    "voice_transcript": "", "gps_lat": None, "gps_lon": None,
    "emergency_contacts": [{"name": "Emergency Contact 1", "phone": ""}],
    "sms_sent_results": [], "location": {"lat":18.5204,"lon":73.8567,"city":"Pune","country":"India"}
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── HERO ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🚨 RoadSoS v3.0</h1>
    <p>AI-Powered Emergency Road Safety Assistant · BIMSTEC Countries</p>
    <span class="badge">✓ AI Severity Detection</span>
    <span class="badge">✓ Golden Hour AI</span>
    <span class="badge-green">✓ Voice SOS</span>
    <span class="badge-green">✓ Live Map + GPS</span>
    <span class="badge-green">✓ SMS Alerts</span>
    <span class="badge">✓ Offline Ready</span>
</div>
""", unsafe_allow_html=True)

# ─── STATS ────────────────────────────────────────────────────────────────────
analytics = get_analytics()
for col, num, lbl in zip(
    st.columns(6),
    ["7","37+","24/7",str(analytics["total"]),"3","⚡"],
    ["Countries","Services","AI Support","Incidents","New Features","Offline"]
):
    with col:
        st.markdown(f'<div class="stat-pill"><span class="num">{num}</span><span class="lbl">{lbl}</span></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📍 Location")
    country = st.selectbox("Country", list(COUNTRY_FLAGS.keys()),
        index=list(COUNTRY_FLAGS.keys()).index(st.session_state.location["country"]))
    city = st.selectbox("City", CITY_MAP.get(country, ["Capital"]))
    coords = CITY_COORDS.get(city, (18.5204, 73.8567))

    # Allow GPS override
    if st.session_state.gps_lat and st.session_state.gps_lon:
        use_gps = st.checkbox("Use GPS coordinates", value=True)
        if use_gps:
            coords = (st.session_state.gps_lat, st.session_state.gps_lon)
            st.success(f"📡 GPS: {coords[0]:.4f}, {coords[1]:.4f}")

    st.session_state.location = {"lat": coords[0], "lon": coords[1], "city": city, "country": country}

    st.markdown("---")
    st.markdown("### ☎️ Emergency Numbers")
    for svc, num in get_emergency_numbers(country):
        st.markdown(f"**{num}** — {svc}")

    st.markdown("---")
    st.markdown("### 🌐 Translate")
    lang_choice = st.selectbox("Language:", list(LANGUAGES.keys()))
    translate_text = st.text_area("Message:", height=70)
    if st.button("Translate 🌐"):
        if translate_text:
            st.session_state.translated_text = translate_emergency(translate_text, LANGUAGES[lang_choice])
    if st.session_state.translated_text:
        st.info(st.session_state.translated_text)

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🆘 Emergency", "🎤 Voice SOS", "🗺️ Live Map", "📩 SMS Alerts", "🤖 AI Chat", "📊 Analytics"
])

# ══════════════════════════════════════════════
# TAB 1 — EMERGENCY RESPONSE
# ══════════════════════════════════════════════
with tab1:
    left, right = st.columns([1.1, 0.9], gap="large")
    with left:
        st.markdown("### ⚡ AI Severity Analyzer")
        incident_text = st.text_area("Describe the accident:", height=100,
            placeholder="e.g. Bike crash, rider unconscious, heavy bleeding, highway NH48...")

        st.markdown("**Quick Scenarios:**")
        qcols = st.columns(3)
        for i, (label, scenario) in enumerate(QUICK_SCENARIOS):
            with qcols[i % 3]:
                if st.button(label, use_container_width=True, key=f"qs_{i}"):
                    incident_text = scenario

        c1, c2 = st.columns([2, 1])
        with c1:
            analyze_clicked = st.button("🔍 Analyze + Get Help", use_container_width=True, type="primary")
        with c2:
            sos_clicked = st.button("🆘 SOS NOW", use_container_width=True)

        if sos_clicked:
            incident_text = f"SOS Emergency in {city}, {country}!"
            analyze_clicked = True

        if analyze_clicked and incident_text:
            with st.spinner("🤖 AI analyzing..."):
                sev = analyze_severity(incident_text)
                st.session_state.severity_result = sev
                trauma = get_nearest_trauma_center(coords[0], coords[1])
                st.session_state.golden_hour = get_golden_hour_analysis(incident_text, trauma, sev)
                st.session_state.golden_trauma = trauma
                st.session_state.first_aid_steps = []
                log_incident(country, city, sev["severity"], sev.get("incident_type","unknown"), ", ".join(sev.get("services_needed",[])))

        if st.session_state.severity_result:
            sev = st.session_state.severity_result
            color = get_severity_color(sev["severity"])
            emoji = SEVERITY_EMOJIS.get(sev["severity"], "🔴")
            st.markdown(f"""
            <div class="severity-card" style="background:linear-gradient(135deg,{color},{color}cc);">
                <div class="severity-score">{sev['severity_score']}</div>
                <h3 style="margin:0;font-family:Syne,sans-serif;">{emoji} {sev['severity']} SEVERITY</h3>
                <p style="margin:0.3rem 0;opacity:0.9;font-size:0.85rem;">{sev.get('reasoning','')}</p>
                <p style="margin:0.5rem 0 0 0;font-size:0.8rem;opacity:0.8;">
                    🏥 {sev.get('incident_type','').replace('_',' ').title()} &nbsp;|&nbsp;
                    ⚠️ Golden Hour Risk: {"YES" if sev.get('golden_hour_risk') else "LOW"}
                </p>
            </div>""", unsafe_allow_html=True)

            injuries = sev.get("injuries_detected", [])
            if injuries:
                st.markdown(f"**🩺 Detected:** {' · '.join(injuries)}")
            st.markdown("**⚡ Immediate Actions:**")
            for i, action in enumerate(sev.get("immediate_actions", []), 1):
                st.markdown(f'<div class="action-step"><div class="step-circle">{i}</div><div>{action}</div></div>', unsafe_allow_html=True)

        if st.session_state.golden_hour:
            trauma = st.session_state.golden_trauma
            t_name = trauma["name"] if trauma else "Nearest Trauma Center"
            dist = trauma["distance_km"] if trauma else "?"
            eta = trauma["eta_minutes"] if trauma else "?"
            phone = trauma["phone"] if trauma else "108"
            st.markdown(f"""
            <div class="golden-box">
                <h3>⏱️ Golden Hour Analysis</h3>
                <p style="margin:0 0 0.5rem 0;font-size:0.85rem;">{st.session_state.golden_hour}</p>
                <hr style="border-color:rgba(255,255,255,0.3);margin:0.8rem 0">
                <b>🏥 Nearest Trauma:</b> {t_name}<br>
                <small>📍 {dist}km · ETA: {format_eta(eta) if isinstance(eta,int) else eta} · 📞 {phone}</small>
            </div>""", unsafe_allow_html=True)

        if st.session_state.severity_result and incident_text:
            with st.expander("🩹 AI First Aid Steps", expanded=True):
                if not st.session_state.first_aid_steps:
                    with st.spinner("Generating..."):
                        st.session_state.first_aid_steps = generate_first_aid_steps(incident_text)
                for i, step in enumerate(st.session_state.first_aid_steps, 1):
                    st.markdown(f'<div class="action-step"><div class="step-circle">{i}</div><div>{step}</div></div>', unsafe_allow_html=True)

    with right:
        st.markdown("### 🗺️ Nearby Services")
        ftype = st.radio("Filter:", ["All","🏥 Hospital","🚑 Ambulance","👮 Police"], horizontal=True)
        tmap = {"All":None,"🏥 Hospital":"hospital","🚑 Ambulance":"ambulance","👮 Police":"police"}
        for s in get_nearby_services(coords[0], coords[1], tmap[ftype], limit=6):
            icon = SERVICE_ICONS.get(s["type"],"📍")
            flag = COUNTRY_FLAGS.get(s["country"],"🌏")
            tb = "⭐ L1" if s.get("trauma_level")==1 else ""
            st.markdown(f"""
            <div class="service-card">
                <span class="dist-tag">{s['distance_km']}km</span>
                <span class="eta-tag">{format_eta(s['eta_minutes'])}</span>
                <h4>{icon} {s['name']} <small style="color:#e74c3c">{tb}</small></h4>
                <p>{flag} {s['city']}, {s['country']} · 📞 {s['phone']}</p>
                <p>📌 {s['address']}</p>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TAB 2 — VOICE SOS 🎤
# ══════════════════════════════════════════════
with tab2:
    st.markdown("### 🎤 Voice SOS — Speak Your Emergency")
    st.markdown("*Uses your browser microphone — works on Chrome/Edge. Press SPACE or click mic button.*")

    vcol1, vcol2 = st.columns([1, 1], gap="large")

    with vcol1:
        # Render voice component
        st.components.v1.html(get_voice_component_html(), height=340, scrolling=False)

        st.markdown("---")
        st.markdown("#### ⌨️ Manual Voice Transcript Entry")
        st.markdown("*If browser mic is unavailable, paste/type what was spoken:*")
        voice_manual = st.text_input("Voice transcript:", placeholder="e.g. Help! Accident! Bleeding badly!", key="voice_manual")

        if voice_manual:
            if detect_crash_keywords(voice_manual):
                st.markdown(f"""<div class="crash-alert">
                🚨 <b>CRASH KEYWORDS DETECTED!</b> Activating emergency protocol...</div>""", unsafe_allow_html=True)
                with st.spinner("AI analyzing..."):
                    sev = analyze_severity(voice_manual)
                    st.session_state.severity_result = sev
                    trauma = get_nearest_trauma_center(coords[0], coords[1])
                    st.session_state.golden_hour = get_golden_hour_analysis(voice_manual, trauma, sev)
                    st.session_state.golden_trauma = trauma
                    log_incident(country, city, sev["severity"], "voice_sos", "ambulance, police")
                st.success("✅ Emergency analysis complete! Check Emergency tab.")
                numbers = get_emergency_numbers(country)
                if numbers:
                    st.error(f"📞 CALL NOW: **{numbers[0][1]}** ({numbers[0][0]})")
            else:
                st.info("No emergency keywords detected. Try: 'accident', 'help', 'bleeding', 'crash'")

    with vcol2:
        st.markdown("#### 🔊 Detected Emergency Keywords")
        st.markdown("""
        <div style="background:#1a1a2e;color:white;border-radius:12px;padding:1.2rem;font-size:0.85rem;line-height:2">
            These words trigger emergency protocol:<br>
            <span style="background:rgba(231,76,60,0.3);padding:2px 8px;border-radius:10px;margin:2px;display:inline-block">accident</span>
            <span style="background:rgba(231,76,60,0.3);padding:2px 8px;border-radius:10px;margin:2px;display:inline-block">crash</span>
            <span style="background:rgba(231,76,60,0.3);padding:2px 8px;border-radius:10px;margin:2px;display:inline-block">help</span>
            <span style="background:rgba(231,76,60,0.3);padding:2px 8px;border-radius:10px;margin:2px;display:inline-block">bleeding</span>
            <span style="background:rgba(231,76,60,0.3);padding:2px 8px;border-radius:10px;margin:2px;display:inline-block">unconscious</span>
            <span style="background:rgba(231,76,60,0.3);padding:2px 8px;border-radius:10px;margin:2px;display:inline-block">injured</span>
            <span style="background:rgba(231,76,60,0.3);padding:2px 8px;border-radius:10px;margin:2px;display:inline-block">emergency</span>
            <span style="background:rgba(231,76,60,0.3);padding:2px 8px;border-radius:10px;margin:2px;display:inline-block">sos</span>
            <span style="background:rgba(231,76,60,0.3);padding:2px 8px;border-radius:10px;margin:2px;display:inline-block">fire</span>
            <span style="background:rgba(231,76,60,0.3);padding:2px 8px;border-radius:10px;margin:2px;display:inline-block">trapped</span>
            <span style="background:rgba(231,76,60,0.3);padding:2px 8px;border-radius:10px;margin:2px;display:inline-block">ambulance</span>
            <span style="background:rgba(231,76,60,0.3);padding:2px 8px;border-radius:10px;margin:2px;display:inline-block">hospital</span>
            <span style="background:rgba(231,76,60,0.3);padding:2px 8px;border-radius:10px;margin:2px;display:inline-block">dying</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 🌍 Supported Languages")
        st.markdown("""
        <div style="background:#f8f9fa;border-radius:12px;padding:1rem;font-size:0.85rem">
            Voice recognition supports:<br>
            🇮🇳 English (India) · Hindi · Bengali<br>
            🇱🇰 Sinhala · 🇳🇵 Nepali<br>
            🇹🇭 Thai · 🇲🇲 Burmese · 🇧🇹 Dzongkha<br><br>
            <i>Change language in browser speech settings</i>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 📱 Quick Dial")
        dial_numbers = get_emergency_numbers(country)
        for svc, num in dial_numbers[:4]:
            st.markdown(f"""
            <div style="background:#e74c3c;color:white;border-radius:10px;padding:0.6rem 1rem;margin:0.3rem 0;font-weight:600;font-size:0.9rem">
                📞 {num} — {svc}
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TAB 3 — LIVE MAP + GPS 🗺️
# ══════════════════════════════════════════════
with tab3:
    st.markdown("### 🗺️ Live Emergency Map")

    mcol1, mcol2 = st.columns([2, 1], gap="large")

    with mcol1:
        # GPS Detection
        st.components.v1.html(get_gps_html(), height=180, scrolling=False)

        st.markdown("---")

        # Map controls
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            map_filter = st.selectbox("Show services:", ["All","Hospitals","Ambulance","Police"])
        with mc2:
            map_zoom = st.slider("Zoom level:", 10, 16, 13)
        with mc3:
            severity_for_map = None
            if st.session_state.severity_result:
                severity_for_map = st.session_state.severity_result.get("severity")
                st.markdown(f"**Severity:** {SEVERITY_EMOJIS.get(severity_for_map,'')} {severity_for_map}")

        type_map_filter = {"All":None,"Hospitals":"hospital","Ambulance":"ambulance","Police":"police"}
        nearby_for_map = get_nearby_services(
            coords[0], coords[1],
            type_map_filter.get(map_filter), limit=10
        )

        # Build and render Folium map
        try:
            import folium
            from streamlit_folium import st_folium
            fmap = build_emergency_map(coords[0], coords[1], nearby_for_map, severity_for_map, map_zoom)
            if fmap:
                map_data = st_folium(fmap, width=700, height=450, returned_objects=["last_object_clicked"])
                if map_data and map_data.get("last_object_clicked"):
                    clicked = map_data["last_object_clicked"]
                    st.info(f"📍 Clicked: {clicked.get('lat',0):.4f}, {clicked.get('lng',0):.4f}")
        except ImportError:
            # Fallback: OpenStreetMap embed
            lat, lon = coords
            osm_url = f"https://www.openstreetmap.org/export/embed.html?bbox={lon-0.05},{lat-0.05},{lon+0.05},{lat+0.05}&layer=mapnik&marker={lat},{lon}"
            st.markdown(f"""
            <div style="border-radius:14px;overflow:hidden;border:2px solid #e74c3c">
                <iframe src="{osm_url}" width="100%" height="450" frameborder="0" style="display:block"></iframe>
            </div>
            <p style="font-size:0.75rem;color:#888;margin-top:4px">
                📦 For interactive map: <code>pip install folium streamlit-folium</code>
            </p>
            """, unsafe_allow_html=True)

    with mcol2:
        st.markdown("#### 📍 Location Details")
        st.markdown(f"""
        <div style="background:#1a1a2e;color:white;border-radius:12px;padding:1.2rem;margin-bottom:1rem">
            <div style="font-size:1.5rem;margin-bottom:0.5rem">{COUNTRY_FLAGS.get(country,'🌏')}</div>
            <b>{city}, {country}</b><br>
            <small style="opacity:0.7">Lat: {coords[0]:.4f} · Lon: {coords[1]:.4f}</small>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 🏥 Nearest Services")
        for s in nearby_for_map[:5]:
            icon = SERVICE_ICONS.get(s["type"],"📍")
            tb = " ⭐" if s.get("trauma_level")==1 else ""
            st.markdown(f"""
            <div class="service-card" style="padding:0.7rem 0.9rem">
                <span class="dist-tag">{s['distance_km']}km</span>
                <h4 style="font-size:0.82rem">{icon} {s['name']}{tb}</h4>
                <p>📞 {s['phone']} · {format_eta(s['eta_minutes'])}</p>
            </div>""", unsafe_allow_html=True)

        # Maps deep link
        gmaps_url = f"https://www.google.com/maps/search/hospital/@{coords[0]},{coords[1]},14z"
        st.link_button("📍 Open Google Maps", gmaps_url, use_container_width=True)

        osm_nav = f"https://www.openstreetmap.org/?mlat={coords[0]}&mlon={coords[1]}#map=15/{coords[0]}/{coords[1]}"
        st.link_button("🗺️ Open OpenStreetMap", osm_nav, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 4 — SMS ALERTS 📩
# ══════════════════════════════════════════════
with tab4:
    st.markdown("### 📩 Emergency SMS Alert System")
    st.markdown("*Send instant SOS alerts to emergency contacts with your location + situation*")

    scol1, scol2 = st.columns([1.1, 0.9], gap="large")

    with scol1:
        st.markdown("#### 👥 Emergency Contacts")
        # Dynamic contact management
        contacts = st.session_state.emergency_contacts
        updated_contacts = []
        for i, contact in enumerate(contacts):
            cc1, cc2, cc3 = st.columns([2, 2, 0.5])
            with cc1:
                name = st.text_input(f"Name {i+1}", value=contact.get("name",""), key=f"cname_{i}", label_visibility="collapsed", placeholder=f"Contact name {i+1}")
            with cc2:
                phone = st.text_input(f"Phone {i+1}", value=contact.get("phone",""), key=f"cphone_{i}", label_visibility="collapsed", placeholder="+91XXXXXXXXXX")
            with cc3:
                if st.button("🗑️", key=f"del_{i}") and len(contacts) > 1:
                    continue
            updated_contacts.append({"name": name, "phone": phone})
        st.session_state.emergency_contacts = updated_contacts

        if st.button("➕ Add Contact", use_container_width=True):
            st.session_state.emergency_contacts.append({"name": f"Contact {len(st.session_state.emergency_contacts)+1}", "phone": ""})
            st.rerun()

        st.markdown("---")
        st.markdown("#### 📝 Emergency Message Preview")
        sev_data = st.session_state.severity_result or {"severity": "HIGH", "injuries_detected": [], "golden_hour_risk": True}
        trauma_data = st.session_state.golden_trauma
        sms_message = build_emergency_sms(st.session_state.location, sev_data, trauma_data)
        st.text_area("SMS Preview:", value=sms_message, height=200, key="sms_preview")

        st.markdown("---")
        st.markdown("#### 🚀 Send Alerts")

        send_col1, send_col2 = st.columns(2)
        with send_col1:
            if st.button("📩 Send via Twilio SMS", use_container_width=True, type="primary"):
                valid_contacts = [c for c in st.session_state.emergency_contacts if c.get("phone","").strip()]
                if not valid_contacts:
                    st.warning("Add at least one phone number!")
                else:
                    with st.spinner("Sending..."):
                        results = send_bulk_alerts(valid_contacts, sms_message)
                        st.session_state.sms_sent_results = results
                    for r in results:
                        if r.get("success"):
                            st.success(f"✅ Sent to {r['name']} ({r['phone']})")
                        elif r.get("fallback"):
                            st.warning(f"⚠️ Twilio not configured. Use WhatsApp links below.")
                        else:
                            st.error(f"❌ Failed: {r.get('error','')}")

        with send_col2:
            if st.button("🟢 Send via WhatsApp", use_container_width=True):
                valid_contacts = [c for c in st.session_state.emergency_contacts if c.get("phone","").strip()]
                if valid_contacts:
                    for c in valid_contacts:
                        wa_link = get_whatsapp_link(c["phone"], sms_message)
                        st.link_button(f"📲 WhatsApp → {c['name']}", wa_link)
                else:
                    st.warning("Add phone numbers first!")

    with scol2:
        st.markdown("#### ⚙️ Twilio SMS Setup")
        st.markdown("""
        <div class="sms-card">
            <h4>📩 Real SMS via Twilio</h4>
            <p style="opacity:0.7;font-size:0.82rem;margin:0 0 0.8rem 0">
                Free trial at twilio.com — 15 free SMS credits
            </p>
            <div style="background:rgba(255,255,255,0.05);border-radius:8px;padding:0.8rem;font-size:0.78rem;font-family:monospace">
                export TWILIO_ACCOUNT_SID=ACxxx<br>
                export TWILIO_AUTH_TOKEN=xxx<br>
                export TWILIO_PHONE_NUMBER=+1xxx
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 📱 Instant Fallback Links")
        st.markdown("*Works without Twilio — opens WhatsApp/SMS on any phone*")

        valid_contacts_display = [c for c in st.session_state.emergency_contacts if c.get("phone","").strip()]
        if valid_contacts_display:
            for c in valid_contacts_display:
                wa = get_whatsapp_link(c["phone"], sms_message)
                sms_l = get_sms_link(c["phone"], sms_message)
                st.markdown(f"""
                <div class="sms-card" style="margin:0.4rem 0;padding:0.8rem">
                    <b>{c['name']}</b> — {c['phone']}<br>
                    <a href="{wa}" target="_blank" style="color:#25D366;font-size:0.8rem">📲 WhatsApp</a> &nbsp;
                    <a href="{sms_l}" style="color:#3498db;font-size:0.8rem">💬 SMS</a>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Add contacts on the left to see fallback links.")

        st.markdown("#### 📋 What Gets Sent")
        st.markdown("""
        <div style="background:#f8f9fa;border-radius:12px;padding:1rem;font-size:0.83rem">
            ✅ Accident severity level<br>
            ✅ Your GPS location + Google Maps link<br>
            ✅ Detected injuries<br>
            ✅ Nearest trauma center + phone<br>
            ✅ Emergency contact numbers<br>
            ✅ Timestamp
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 🌍 Google Maps Location Link")
        lat, lon = coords
        maps_link = f"https://maps.google.com/?q={lat},{lon}"
        st.markdown(f"**Your location:** [{lat:.4f}, {lon:.4f}]({maps_link})")
        st.link_button("📍 View on Google Maps", maps_link, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 5 — AI CHAT
# ══════════════════════════════════════════════
with tab5:
    st.markdown("### 🤖 RoadSoS AI Assistant")
    if not st.session_state.messages:
        st.markdown("""<div class="chat-bot">
        👋 Hi! I'm RoadSoS AI. I help with emergencies, first aid, and safety across BIMSTEC countries.<br><br>
        🚑 Emergency services · 🩹 First aid · 📞 Emergency numbers · ⚠️ Accident guidance
        </div>""", unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages[-10:]:
            css = "chat-user" if msg["role"] == "user" else "chat-bot"
            icon = "🧑" if msg["role"] == "user" else "🤖"
            st.markdown(f'<div class="{css}">{icon} {msg["content"]}</div>', unsafe_allow_html=True)

    qc = st.columns(3)
    for i, q in enumerate(["What to do if not breathing?","Control heavy bleeding?","Person trapped in vehicle?","Signs of internal injury?","Help fracture victim?","Ambulance is 30 min away?"]):
        with qc[i%3]:
            if st.button(q, key=f"qq_{i}", use_container_width=True):
                st.session_state.messages.append({"role":"user","content":q})
                with st.spinner("Thinking..."):
                    reply = chat_response(st.session_state.messages[:-1], q, st.session_state.location)
                st.session_state.messages.append({"role":"assistant","content":reply})
                st.rerun()

    with st.form("chat_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([5,1,1])
        with c1:
            user_msg = st.text_input("Ask anything...", label_visibility="collapsed", placeholder="Describe your situation or ask for guidance")
        with c2:
            send = st.form_submit_button("Send 📤", use_container_width=True)
        with c3:
            clear = st.form_submit_button("Clear 🗑️", use_container_width=True)
        if send and user_msg:
            st.session_state.messages.append({"role":"user","content":user_msg})
            with st.spinner("Responding..."):
                reply = chat_response(st.session_state.messages[:-1], user_msg, st.session_state.location)
            st.session_state.messages.append({"role":"assistant","content":reply})
            st.rerun()
        if clear:
            st.session_state.messages = []
            st.rerun()

# ══════════════════════════════════════════════
# TAB 6 — ANALYTICS
# ══════════════════════════════════════════════
with tab6:
    st.markdown("### 📊 Incident Analytics Dashboard")
    analytics = get_analytics()
    for col, num, lbl in zip(st.columns(3),
        [str(analytics["total"]), str(next((c for s,c in analytics["by_severity"] if s=="CRITICAL"),0)), str(len(analytics["by_country"]))],
        ["Total Incidents","Critical Cases","Countries Active"]):
        with col:
            st.markdown(f'<div class="stat-pill"><span class="num">{num}</span><span class="lbl">{lbl}</span></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    la, ra = st.columns(2)

    with la:
        st.markdown("#### 🌏 By Country")
        if analytics["by_country"]:
            for cn, count in analytics["by_country"]:
                pct = int((count/max(analytics["total"],1))*100)
                st.markdown(f"""
                <div style="margin:0.4rem 0">
                    <div style="display:flex;justify-content:space-between;margin-bottom:3px"><span>{COUNTRY_FLAGS.get(cn,'🌏')} {cn}</span><span><b>{count}</b></span></div>
                    <div style="background:#f0f0f0;border-radius:10px;height:8px"><div style="background:#e74c3c;width:{pct}%;height:8px;border-radius:10px"></div></div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No incidents yet. Use Emergency tab to log incidents.")

    with ra:
        st.markdown("#### ⚠️ By Severity")
        sev_dict = dict(analytics["by_severity"])
        for s in ["CRITICAL","HIGH","MODERATE","LOW"]:
            count = sev_dict.get(s, 0)
            color = get_severity_color(s)
            pct = int((count/max(analytics["total"],1))*100)
            st.markdown(f"""
            <div style="margin:0.4rem 0">
                <div style="display:flex;justify-content:space-between;margin-bottom:3px"><span>{SEVERITY_EMOJIS.get(s,'')} {s}</span><span><b>{count}</b></span></div>
                <div style="background:#f0f0f0;border-radius:10px;height:8px"><div style="background:{color};width:{pct}%;height:8px;border-radius:10px"></div></div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🌏 BIMSTEC Service Coverage")
    cov_cols = st.columns(7)
    for i, (cn, cd) in enumerate({"India":{"c":3,"s":14},"Bangladesh":{"c":2,"s":5},"Sri Lanka":{"c":1,"s":4},"Nepal":{"c":1,"s":4},"Myanmar":{"c":1,"s":3},"Thailand":{"c":1,"s":4},"Bhutan":{"c":1,"s":3}}.items()):
        with cov_cols[i]:
            st.markdown(f"""
            <div style="text-align:center;background:#f8f9fa;border-radius:10px;padding:0.7rem 0.2rem">
                <div style="font-size:1.4rem">{COUNTRY_FLAGS.get(cn,'🌏')}</div>
                <div style="font-size:0.65rem;font-weight:600;margin:0.2rem 0">{cn}</div>
                <div style="font-size:0.6rem;color:#e74c3c">{cd['s']} services</div>
            </div>""", unsafe_allow_html=True)

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='text-align:center;color:#888;font-size:0.78rem;padding:1rem 0'>
    🚨 <b>RoadSoS v3.0</b> — Road Safety Hackathon 2026 · CoERS, IIT Madras · BIMSTEC<br>
    Voice SOS · Live Map · SMS Alerts · AI Severity · Golden Hour · Multilingual<br>
    <span style='color:#e74c3c'>In a life-threatening emergency, always call local emergency services first.</span>
</div>
""", unsafe_allow_html=True)
