import json
import streamlit as st
import requests

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ApplyFlow",
    page_icon="🚀",
    layout="wide",
)

API_URL = st.secrets.get("API_URL", "http://localhost:8000")

# ── Password protection ───────────────────────────────────────────────────────
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.title("🚀 ApplyFlow")
    st.subheader("Login")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if pwd == st.secrets.get("APP_PASSWORD", "applyflow"):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")
    return False

if not check_password():
    st.stop()

# ── API helpers ───────────────────────────────────────────────────────────────
def api_get(path: str, params: dict = None):
    try:
        r = requests.get(f"{API_URL}{path}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None

def api_post(path: str, data: dict = None):
    try:
        r = requests.post(f"{API_URL}{path}", json=data, timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None

def api_patch(path: str, data: dict = None):
    try:
        r = requests.patch(f"{API_URL}{path}", json=data, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("🚀 ApplyFlow")
st.sidebar.caption("Job application pipeline")

if st.sidebar.button("▶ Run Pipeline Now", use_container_width=True):
    with st.spinner("Fetching and scoring jobs..."):
        result = api_post("/jobs/ingest")
    if result and result.get("success"):
        st.sidebar.success("Pipeline complete!")
    else:
        st.sidebar.error("Pipeline failed")

# Health status
health = api_get("/health")
if health:
    status_color = "🟢" if health["status"] == "ok" else "🔴"
    st.sidebar.caption(f"{status_color} DB: {health['db']}")
    st.sidebar.caption(f"Last check: {health['timestamp'][:19]}")

st.sidebar.divider()

# Filters
st.sidebar.subheader("Filters")
jobs_data = api_get("/jobs") or {"jobs": []}
all_jobs = jobs_data.get("jobs", [])

companies = ["All"] + sorted({a["company"] for a in all_jobs})
selected_company = st.sidebar.selectbox("Company", companies)

statuses = ["All", "new", "applied", "phone_screen", "technical", "final_round", "rejected", "offer"]
selected_status = st.sidebar.selectbox("Status", statuses)

min_score = st.sidebar.slider("Min match score", 0, 100, 0)

# ── Main area ─────────────────────────────────────────────────────────────────
st.title("🚀 ApplyFlow")

# Metrics row
analytics = api_get("/analytics/conversion") or {}
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Jobs", analytics.get("total", len(all_jobs)))
c2.metric("Applied", analytics.get("applied", 0))
c3.metric("Interviews", analytics.get("interviewed", 0))
c4.metric("Offers", analytics.get("offers", 0))

st.divider()

# Skills gap
skills_data = api_get("/analytics/skills-gap") or {}
top_missing = skills_data.get("top_missing_skills", [])
if top_missing:
    with st.expander("📊 Top missing skills across all jobs"):
        cols = st.columns(5)
        for i, item in enumerate(top_missing[:10]):
            cols[i % 5].metric(item["skill"], item["count"])

st.divider()

# Apply filters
filtered = all_jobs
if selected_company != "All":
    filtered = [a for a in filtered if a["company"] == selected_company]
if selected_status != "All":
    filtered = [a for a in filtered if a["status"] == selected_status]
filtered = [a for a in filtered if a["match_score"] >= min_score]

st.subheader(f"Jobs ({len(filtered)} shown)")

if not filtered:
    st.info("No jobs match your filters.")
else:
    for a in filtered:
        score = a["match_score"]
        color = "green" if score >= 70 else "orange" if score >= 40 else "red"

        with st.expander(f"[{score:.0f}]  {a['company'].upper()}  —  {a['title']}"):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"📍 `{a['location']}`")
                st.markdown(f"🔗 [View job posting]({a['source_url']})")

                missing = json.loads(a.get("missing_skills") or "[]")
                matched = json.loads(a.get("matched_skills") or "[]")

                if matched:
                    st.markdown("✅ **Matched:** " + ", ".join(matched))
                if missing:
                    st.markdown("❌ **Missing:** " + ", ".join(missing))
                if a.get("experience_gap"):
                    st.warning(f"⚠️ YOE gap: {a['experience_gap']} years")

            with col2:
                st.markdown(f"### :{color}[{score:.0f}]")
                st.caption("match score")

                new_status = st.selectbox(
                    "Status",
                    statuses[1:],
                    index=statuses[1:].index(a["status"]) if a["status"] in statuses[1:] else 0,
                    key=f"status_{a['job_id']}",
                )
                if new_status != a["status"]:
                    api_patch(
                        f"/applications/{a['job_id']}",
                        {"status": new_status}
                    )
                    st.rerun()