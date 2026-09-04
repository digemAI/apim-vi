import streamlit as st
import engine.dojo as dojo
from engine.core import classify, recommendations, compute_dimensions
from engine.dojo import demo_forward_pass, train_on_startup
from engine.dojo import predict_v3
from engine.storage import save_shadow
from engine.storage import save_run, save_feedback

# We don't show the Principles button for Strategist / Boss, but we still store it in case it's needed later
def should_show_principles(profile: str) -> bool:
    return profile not in ["Money Boss", "Financial Strategist"]

# Basic configuration
st.set_page_config(page_title="APIM VI", page_icon="💸", layout="centered")
st.title("APIM VI - Smart Financial Test")

# Form
with st.form("apim_form"):
    st.subheader("Enter your answers")

    savings_pct = st.slider("What % of your income do you save monthly?", 0, 50, 10)
    impulsive_purchases = st.number_input("Impulsive purchases per week", min_value=0, max_value=50, value=1, step=1)
    tracks_expenses = st.checkbox("I track my expenses (even just in notes)")
    fund_months = st.slider("Emergency fund (months covered)", 0, 12, 3)

    submitted = st.form_submit_button("Classify")


# When classifying, we compute and save to session + JSON history
if submitted:
    answers = {
        "monthly_savings_pct": int(savings_pct),
        "impulsive_purchases_week": int(impulsive_purchases),
        "tracks_expenses": bool(tracks_expenses),
        "emergency_fund_months": int(fund_months),
    }
    # Main classification and personalized recommendations
    result = classify(answers)
    dimensions = compute_dimensions(answers)
    reco = recommendations(result.profile, answers, dimensions)

    # Save everything to session
    st.session_state["answers"] = answers
    st.session_state["result"] = result
    st.session_state["reco"] = reco
    st.session_state["dimensions"] = dimensions

    # Save the run once
    run_id = save_run(answers, result)
    st.session_state["run_id"] = run_id

    # Silent V3 shadow prediction
    try:
        v3_pred = predict_v3(answers)
        save_shadow(run_id, v3_pred, result.profile)
    except Exception:
        pass


# Results
if "result" in st.session_state:
    result = st.session_state["result"]
    reco = st.session_state["reco"]
    answers = st.session_state["answers"]
    run_id = st.session_state.get("run_id", "")

    st.subheader("Your profile")
    st.write(result.profile)
    st.caption(result.summary)

    st.subheader("APIM Score")
    st.write(result.score)

    # Per-dimension breakdown (V2): shows why the score landed where it did.
    dimensions = st.session_state.get("dimensions")
    if dimensions:
        st.subheader("📊 Dimension Breakdown")
        for label, value in dimensions["scores"].items():
            st.progress(value / 10, text=f"{label}: {value}/10")
        st.caption(
            f"Strength: **{dimensions['strongest_dimension']}** · "
            f"To work on: **{dimensions['weakest_dimension']}**"
        )

    # Explanatory, visual Dojo demo.
    # Expander rule: supplementary/demo content starts collapsed (this one);
    # user-actionable content (Priority focus, below) starts expanded.
    with st.expander("🤖 AI Touches (Dojo)", expanded=False):
        output, distance_score = demo_forward_pass(answers)
        st.write("Dojo signal (demo):")
        st.code(str(output))
        st.write(f"Closeness score (demo): **{distance_score:.4f}**")


    # Actionable recommendations, shown as tabs instead of hand-rolled toggle
    # buttons: st.tabs() gives a native "which one is active" indicator for
    # free and keeps the heading attached to content that's always visible.
    st.markdown("## Actionable recommendations")

    tab_labels = ["🔥 Actions today", "🗓️ 7-day plan", "📆 30-day plan"]
    if should_show_principles(result.profile):
        tab_labels.append("📖 Principles")

    tabs = st.tabs(tab_labels)

    with tabs[0]:
        for a in reco["immediate_actions"]:
            st.markdown(f"- {a}")

    with tabs[1]:
        for p in reco["plan_7_days"]:
            st.markdown(f"- {p}")

    with tabs[2]:
        for p in reco["plan_30_days"]:
            st.markdown(f"- {p}")

    if should_show_principles(result.profile):
        with tabs[3]:
            for pr in reco["principles"]:
                st.markdown(f"- {pr}")

    # Priority focus (single weakest dimension, V4)
    st.markdown("---")
    with st.expander("🎯 Priority focus", expanded=True):
        for e in reco["focus"]:
            st.markdown(f"- {e}")

    # User feedback
    st.markdown("---")
    st.subheader("✍️ Quick feedback")

    rating = st.slider("How useful was this result?", 1, 5, 4)
    comment = st.text_input("Optional comment (1 line):", "")

    if st.button("Save feedback"):
        if run_id:
            save_feedback(run_id, rating, comment)
            st.success(" ✅ Thanks for your feedback")
        else:
            st.warning("Classify first to generate a run_id.")