import subprocess
import sys

import streamlit as st

from domain.application import ApplicationStatus
from infrastructure.database import init_db
from infrastructure.repositories import ApplicationRepository, JobRepository

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ApplyFlow",
    page_icon="🚀",
    layout="wide",
)

init_db()
job_repo = JobRepository()
app_repo = ApplicationRepository()


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("🚀 ApplyFlow")
st.sidebar.caption("Job application pipeline")

if st.sidebar.button("▶ Run Pipeline Now", use_container_width=True):
    with st.spinner("Fetching and scoring jobs..."):
        result = subprocess.run(
            [sys.executable, "main.py"],
            capture_output=True, text=True
        )
    if result.returncode == 0:
        st.sidebar.success("Pipeline complete!")
    else:
        st.sidebar.error("Pipeline failed — check logs")
        st.sidebar.code(result.stderr)

st.sidebar.divider()

# Filters
st.sidebar.subheader("Filters")
companies = ["All"] + sorted({
    a["company"] for a in app_repo.get_all()
})
selected_company = st.sidebar.selectbox("Company", companies)

statuses = ["All"] + [s.value for s in ApplicationStatus]
selected_status = st.sidebar.selectbox("Status", statuses)

min_score = st.sidebar.slider("Min match score", 0, 100, 0)


# ── Main area ─────────────────────────────────────────────────────────────────
st.title("🚀 ApplyFlow")

# Metrics row
apps = app_repo.get_all()
total = len(apps)
applied = sum(1 for a in apps if a["status"] == ApplicationStatus.APPLIED.value)
interviewed = sum(1 for a in apps if a["status"] in [
    ApplicationStatus.PHONE_SCREEN.value,
    ApplicationStatus.TECHNICAL.value,
    ApplicationStatus.FINAL_ROUND.value,
])
offers = sum(1 for a in apps if a["status"] == ApplicationStatus.OFFER.value)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Jobs", total)
c2.metric("Applied", applied)
c3.metric("Interviews", interviewed)
c4.metric("Offers", offers)

st.divider()

# Apply filters
filtered = apps
if selected_company != "All":
    filtered = [a for a in filtered if a["company"] == selected_company]
if selected_status != "All":
    filtered = [a for a in filtered if a["status"] == selected_status]
filtered = [a for a in filtered if a["match_score"] >= min_score]

st.subheader(f"Jobs ({len(filtered)} shown)")

# Job cards
if not filtered:
    st.info("No jobs match your filters.")
else:
    for a in filtered:
        score = a["match_score"]
        color = "green" if score >= 70 else "orange" if score >= 40 else "red"

        with st.expander(
            f"[{score:.0f}]  {a['company'].upper()}  —  {a['title']}"
        ):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"📍 `{a['location']}`")
                st.markdown(f"🔗 [View job posting]({a['source_url']})")

                import json
                missing = json.loads(a.get("missing_skills") or "[]")
                matched = json.loads(a.get("matched_skills") or "[]")

                if matched:
                    st.markdown("✅ **Matched skills:** " + ", ".join(matched))
                if missing:
                    st.markdown("❌ **Missing skills:** " + ", ".join(missing))
                if a["experience_gap"]:
                    st.warning(f"⚠️ YOE gap: {a['experience_gap']} years")

            with col2:
                st.markdown(f"### :{color}[{score:.0f}]")
                st.caption("match score")

                new_status = st.selectbox(
                    "Status",
                    [s.value for s in ApplicationStatus],
                    index=[s.value for s in ApplicationStatus].index(a["status"]),
                    key=f"status_{a['job_id']}",
                )
                if new_status != a["status"]:
                    app_repo.update_status(
                        a["job_id"], ApplicationStatus(new_status)
                    )
                    st.rerun()