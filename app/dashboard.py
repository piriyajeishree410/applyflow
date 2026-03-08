import json
import io
import streamlit as st
import requests

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ApplyFlow",
    page_icon="🚀",
    layout="wide",
)

API_URL = st.secrets.get("API_URL", "http://localhost:8000")
USER_ID = "jeishree"

# ── Password protection ───────────────────────────────────────────────────────
def check_password():
    if st.session_state.get("authenticated"):
        return True
    # Hide sidebar on login screen
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {display: none}
        </style>
    """, unsafe_allow_html=True)
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

# ── Sidebar ───────────────────────────────────────────────────────────────────
def api_get(path, params=None):
    try:
        r = requests.get(f"{API_URL}{path}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None

def api_post(path, data=None):
    try:
        r = requests.post(f"{API_URL}{path}", json=data, timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None

def api_patch(path, data=None):
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

page = st.sidebar.radio(
    "Navigation",
    ["🔍 Job Feed", "👤 My Profile"],
    label_visibility="collapsed"
)

st.sidebar.divider()

if st.sidebar.button("▶ Run Pipeline Now", use_container_width=True):
    with st.spinner("Fetching and scoring jobs..."):
        result = api_post("/jobs/ingest")
    if result and result.get("success"):
        st.sidebar.success("Pipeline complete!")
    else:
        st.sidebar.error("Pipeline failed")

health = api_get("/health")
if health:
    color = "🟢" if health["status"] == "ok" else "🔴"
    st.sidebar.caption(f"{color} DB: {health['db']}")
    st.sidebar.caption(f"Last check: {health['timestamp'][:19]}")

# ── Profile Page ──────────────────────────────────────────────────────────────
if page == "👤 My Profile":
    st.title("👤 My Profile")
    existing = api_get(f"/profiles/{USER_ID}")

    with st.form("profile_form"):
        st.subheader("Basic Info")
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input(
                "Name",
                value=existing["name"] if existing else ""
            )
            experience_years = st.number_input(
                "Years of experience", min_value=0, max_value=20,
                value=existing["experience_years"] if existing else 0
            )
        with c2:
            experience_level = st.selectbox(
                "Experience level", ["intern", "entry", "mid"],
                index=["intern", "entry", "mid"].index(
                    existing["experience_level"] if existing else "entry"
                )
            )
            location_pref = st.selectbox(
                "Location preference", ["any", "remote", "hybrid", "onsite"],
                index=["any", "remote", "hybrid", "onsite"].index(
                    existing["location_pref"] if existing else "any"
                )
            )

        st.subheader("Role Targeting")
        role_keywords = st.text_input(
            "Role keywords (comma separated)",
            value=", ".join(existing["role_keywords"]) if existing
                else "SRE, DevOps, Cloud Engineer, Infrastructure",
            help="Jobs matching these keywords will be collected"
        )
        required_stack = st.text_input(
            "Required tech stack (comma separated)",
            value=", ".join(existing["required_stack"]) if existing
                else "Docker, Terraform, AWS, Python",
        )
        preferred_stack = st.text_input(
            "Preferred stack (comma separated)",
            value=", ".join(existing["preferred_stack"]) if existing
                else "Kubernetes, GitHub Actions",
        )

        st.subheader("🏢 Companies to Track")
        st.caption("Search for any company that uses Greenhouse for hiring")

        # Company search
        search_col, btn_col = st.columns([3, 1])
        with search_col:
            company_search = st.text_input(
                "Search company",
                placeholder="e.g. stripe, figma, notion, airbnb...",
                key="company_search",
                label_visibility="collapsed"
            )
        with btn_col:
            check_btn = st.button("Check", use_container_width=True)

        if check_btn and company_search:
            result = api_get(
                "/jobs/check-company",
                params={"name": company_search.strip().lower()}
            )
            if result and result["found"]:
                st.success(
                    f"✅ {company_search} uses Greenhouse — "
                    f"{result['job_count']} jobs available. Add it below!"
                )
            elif result:
                st.error(
                    f"❌ {company_search} not found on Greenhouse. "
                    "Try a different name (use their careers page URL slug)."
                )

        default_companies = ", ".join(existing["companies"]) if existing and existing.get("companies") \
            else "cloudflare, datadog, elastic, mongodb"
        companies_input = st.text_area(
            "Companies to track (comma separated)",
            value=default_companies,
            height=80,
            help="These companies will be checked for new jobs every 6 hours"
        )

        st.subheader("Resume Skills")
        skills_input = st.text_area(
            "Your skills (comma separated)",
            value=", ".join(existing["skills"]) if existing
                else "docker, terraform, aws, python, github actions, cloudwatch, ecs, bash, git, linux",
            height=100,
        )
        certifications = st.text_input(
            "Certifications (comma separated)",
            value=", ".join(existing["certifications"]) if existing
                else "AWS Certified Cloud Practitioner"
        )

        st.subheader("📄 Resume Upload")
        uploaded_file = st.file_uploader(
            "Upload your resume PDF — skills auto-extracted",
            type=["pdf"],
        )

        submitted = st.form_submit_button("💾 Save Profile", use_container_width=True)

        if submitted:
            extracted_skills = []
            if uploaded_file:
                try:
                    import pypdf
                    reader = pypdf.PdfReader(io.BytesIO(uploaded_file.read()))
                    text = " ".join(
                        page.extract_text() or "" for page in reader.pages
                    )
                    from services.parser import extract_skills
                    extracted_skills = extract_skills(text)
                    st.info(
                        f"Extracted {len(extracted_skills)} skills: "
                        f"{', '.join(extracted_skills[:8])}..."
                    )
                except Exception as e:
                    st.warning(f"Could not parse PDF: {e}")

            manual = [s.strip().lower() for s in skills_input.split(",") if s.strip()]
            all_skills = list(set(manual + extracted_skills))

            result = api_post("/profiles", {
                "user_id": USER_ID,
                "name": name,
                "role_keywords": [k.strip() for k in role_keywords.split(",") if k.strip()],
                "required_stack": [s.strip() for s in required_stack.split(",") if s.strip()],
                "preferred_stack": [s.strip() for s in preferred_stack.split(",") if s.strip()],
                "experience_level": experience_level,
                "location_pref": location_pref,
                "skills": all_skills,
                "experience_years": int(experience_years),
                "certifications": [c.strip() for c in certifications.split(",") if c.strip()],
                "companies": [c.strip().lower() for c in companies_input.split(",") if c.strip()],
            })
            if result:
                st.success("Profile saved!")
                st.rerun()

    if existing:
        st.divider()
        st.subheader("Current Profile")
        c1, c2, c3 = st.columns(3)
        c1.metric("Experience", f"{existing['experience_years']} yrs")
        c2.metric("Level", existing["experience_level"].capitalize())
        c3.metric("Skills tracked", len(existing["skills"]))
        st.caption(f"Targeting: {', '.join(existing['role_keywords'])}")
        st.caption(f"Stack: {', '.join(existing['skills'][:10])}...")

# ── Job Feed Page ─────────────────────────────────────────────────────────────
elif page == "🔍 Job Feed":
    st.title("🚀 ApplyFlow")

    # Metrics
    analytics = api_get("/analytics/conversion") or {}
    jobs_data = api_get("/jobs") or {"jobs": []}
    all_jobs = jobs_data.get("jobs", [])

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

    # Filters
    st.sidebar.subheader("Filters")
    companies = ["All"] + sorted({a["company"] for a in all_jobs})
    selected_company = st.sidebar.selectbox("Company", companies)
    statuses = ["All", "new", "applied", "phone_screen", "technical",
                "final_round", "rejected", "offer"]
    selected_status = st.sidebar.selectbox("Status", statuses)
    min_score = st.sidebar.slider("Min match score", 0, 100, 0)

    # Apply filters
    filtered = all_jobs
    if selected_company != "All":
        filtered = [a for a in filtered if a["company"] == selected_company]
    if selected_status != "All":
        filtered = [a for a in filtered if a["status"] == selected_status]
    filtered = [a for a in filtered if a["match_score"] >= min_score]

    # Keyword search
    search = st.text_input(
        "🔍 Search jobs",
        placeholder="e.g. kubernetes, platform, senior..."
    )
    if search:
        terms = [t.strip().lower() for t in search.split(",")]
        filtered = [
            a for a in filtered
            if any(
                t in a["title"].lower() or t in a["company"].lower()
                for t in terms
            )
        ]

    st.subheader(f"Jobs ({len(filtered)} shown)")

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
                        index=statuses[1:].index(a["status"])
                            if a["status"] in statuses[1:] else 0,
                        key=f"status_{a['job_id']}",
                    )
                    if new_status != a["status"]:
                        api_patch(
                            f"/applications/{a['job_id']}",
                            {"status": new_status}
                        )
                        st.rerun()