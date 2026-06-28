from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


# Final result structure used by the Streamlit app.
@dataclass
class Result:
    profile: str
    score: int
    summary: str


# 1) MAIN CLASSIFIER (V1)
def classify(answers: Dict[str, Any]) -> Result:
    """
    Applies the base APIM VI rules and returns the user's financial profile.
    """
    score = 0

    # Read input values with safe defaults in case some keys are missing.
    savings_pct = answers.get("monthly_savings_pct", 0)              # 0-50
    impulsive_purchases = answers.get("impulsive_purchases_week", 0) # 0-14
    tracks_expenses = answers.get("tracks_expenses", False)          # bool
    emergency_fund_months = answers.get("emergency_fund_months", 0)  # 0-12

    # Savings: step up the score for >=10% and >=20%.
    if savings_pct >= 10:
        score += 3
    if savings_pct >= 20:
        score += 2

    # Impulse purchases: downweight the score for frequent emotional spending.
    if impulsive_purchases >= 3:
        score -= 3
    if impulsive_purchases >= 7:
        score -= 2

    # Expense tracking: boost the score for maintaining visibility over cash flow.
    if tracks_expenses:
        score += 2

    # Emergency fund: bump the score for 3 and 6-month buffers.
    if emergency_fund_months >= 3:
        score += 3
    if emergency_fund_months >= 6:
        score += 2

    # Classify the raw score into a discrete profile.
    if score <= 0:
        profile = "Impulse Buyer"
        summary = (
            "You have potential, but money leaves too fast through impulse decisions. "
            "The goal is to control that pattern."
        )
    elif 1 <= score <= 4:
        profile = "Disciplined Saver"
        summary = (
            "You are building solid habits. With consistency and a few adjustments, "
            "your financial control can improve quickly."
        )
    elif 5 <= score <= 7:
        profile = "Financial Strategist"
        summary = (
            "You make solid decisions and maintain useful habits. "
            "The next step is turning control into opportunity."
        )
    else:
        profile = "Money Boss"
        summary = (
            "You show strong control. Now the challenge is to protect, optimize, "
            "and scale what you are already doing well."
        )

    return Result(profile=profile, score=score, summary=summary)


# 2) WEAKNESS DETECTOR (V2 helper)
def detect_weaknesses(answers: Dict[str, Any]) -> List[str]:
    """
    Identifies key financial vulnerabilities based on the survey data
    """
    weaknesses: List[str] = []

    # Normalizes the dictionary inputs into typed metrics.
    savings = int(answers.get("monthly_savings_pct", 0))         # %
    impulsive = int(answers.get("impulsive_purchases_week", 0))  # times/week
    tracks = bool(answers.get("tracks_expenses", False))         # True/False
    fund = float(answers.get("emergency_fund_months", 0))        # months

    # Evaluates baseline thresholds, pending future calibration.
    if impulsive >= 3:
        weaknesses.append("impulse_spending")

    if not tracks:
        weaknesses.append("no_expense_tracking")

    # Flags buffers under 1 month as missing.
    if fund < 1:
        weaknesses.append("no_emergency_fund")

    # Flags <10% savings as a weakness.
    if savings < 10:
        weaknesses.append("low_savings")

    return weaknesses


# 3) RECOMMENDATIONS (V2)
def recommendations(profile: str, answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds personalized recommendations using basic financial education rules.

    Main ideas:
    - Pay yourself first.
    - Save 10-20% when possible.
    - Use a 48-hour rule before impulse purchases.
    - Ask two questions before spending.
    - Separate money by purpose.
    - Use compounding: small decisions + consistency + time.
    """
    weaknesses = detect_weaknesses(answers)

    # Recommendations by financial profile.
    by_profile: Dict[str, Dict[str, List[str]]] = {
        "Impulse Buyer": {
            "immediate_actions": [
                "Apply the 48-hour rule: do not buy anything above your limit without waiting two days.",
                "Before buying, ask yourself: 1) Does this make me richer or poorer? 2) Do I really want this, or am I trying to feel better?",
                "Use cash when possible. Paying with physical money makes the decision more visible.",
            ],
            "plan_7_days": [
                "Day 1: Write down every expense, even if you only use your notes app.",
                "Day 2: Identify three emotional expenses and remove them this week.",
                "Day 3: Set a weekly limit for cravings or non-essential purchases.",
                "Day 4: Apply the 48-hour rule to online carts and impulse purchases.",
                "Day 5: Review your expenses and mark which ones move you closer to or away from your goals.",
                "Day 6: Ask the two spending questions before any non-essential purchase.",
                "Day 7: Review how much you avoided spending by adding friction to impulse decisions.",
            ],
            "plan_30_days": [
                "Define a fixed savings percentage, starting with at least 10% if possible.",
                "Start building an emergency fund. First target: one month of basic expenses.",
                "Choose one clear goal, such as debt reduction, an emergency fund, or a first investment.",
            ],
        },
        "Disciplined Saver": {
            "immediate_actions": [
                "Formalize the 'pay yourself first' habit: separate at least 10% of your income when it arrives.",
                "Review your expenses and remove one subscription or recurring cost that no longer makes sense.",
                "Write down your main financial goal, such as a three-month emergency fund, a first investment, or debt reduction.",
            ],
            "plan_7_days": [
                "Day 1: Build a simple overview: income, fixed expenses, and variable expenses.",
                "Day 2: Adjust your savings percentage and define a small amount for fun without guilt.",
                "Day 3: Create or label an account for long-term financial freedom.",
                "Day 4: Identify expensive debt and plan how to reduce it faster.",
                "Day 5: Review whether your expenses reflect what actually matters to you.",
                "Day 6: Set spending limits by category: home, food, transport, and leisure.",
                "Day 7: Review the week and identify the habit that gave you the most control.",
            ],
            "plan_30_days": [
                "Aim to save between 10% and 20% of your total income when possible.",
                "Reach the first emergency fund milestone: one month of basic expenses.",
                "Learn one financial education concept per week and apply it in a small way.",
            ],
        },
        "Financial Strategist": {
            "immediate_actions": [
                "Write down your target percentages for needs, fun, long-term investing, and financial freedom.",
                "Review fees and taxes from your current financial products and remove anything that drains more than it helps.",
                "Choose one simple investment vehicle and define a monthly amount for it.",
            ],
            "plan_7_days": [
                "Day 1: Build a personal financial snapshot: assets, liabilities, income, and expenses.",
                "Day 2: Classify expenses into deficit areas and surplus areas.",
                "Day 3: Adjust your budget so monthly surplus becomes intentional.",
                "Day 4: Review the difference between earned income, portfolio income, and passive income.",
                "Day 5: Review whether your decisions support compounding: small improvements repeated over time.",
                "Day 6: Review risks and insurance to protect what you are building.",
                "Day 7: Document what you learned and choose one improvement for next month.",
            ],
            "plan_30_days": [
                "Consolidate an emergency fund of at least one to three months.",
                "Start or reinforce a diversified long-term investment strategy.",
                "Create a weekly money review habit, such as 20 minutes every Sunday.",
            ],
        },
        "Money Boss": {
            "immediate_actions": [
                "Align your money decisions with your deeper purpose, not only with the number.",
                "Define one major financial objective and two metrics you will monitor.",
                "Document your money flow: what comes in, what goes out, and what builds assets.",
            ],
            "plan_7_days": [
                "Day 1: Review whether your time is aligned with producing, protecting, budgeting, leveraging, and learning.",
                "Day 2: Ask yourself: am I building assets or only maintaining expensive habits?",
                "Day 3: Adjust your flows so liabilities are supported by assets, not only by salary.",
                "Day 4: Design one additional income system, such as a business, project, or skill.",
                "Day 5: Review your circle: who do you talk to about money, and what mindset do they bring?",
                "Day 6: Adjust your plan based on your energy and reality, not on trends.",
                "Day 7: Review whether your actions move you closer to the life you want, not only the number you want.",
            ],
            "plan_30_days": [
                "Strengthen at least one real asset: business, real estate, paper assets, or intellectual property.",
                "Define a yearly plan with goals, quarterly milestones, and monthly reviews.",
                "Make financial education a stable habit, not a temporary streak.",
            ],
        },
    }

    # Fall back to Disciplined Saver if an unknown profile arrives.
    block = by_profile.get(profile, by_profile["Disciplined Saver"])

    # General APIM principles. These apply to every profile.
    principles: List[str] = [
        "Pay yourself first: reserve part of your income before paying everyone else.",
        "Small good decisions + consistency + time = a radical difference.",
        "Before spending, ask yourself: does this make me richer or poorer? Do I really want it, or am I trying to feel better?",
        "Never make important money decisions from the emotion of the moment.",
        "Use money as a tool for the life you want, not as a measure of your value.",
    ]

    # Personalized focus based on detected weaknesses.
    focus: List[str] = []

    if "impulse_spending" in weaknesses:
        focus.append(
            "Your weak point is impulse spending: apply the 48-hour rule and ask the two spending questions before buying."
        )
    if "no_expense_tracking" in weaknesses:
        focus.append(
            "You are not tracking expenses: seven days of total tracking can make your money flow visible."
        )
    if "no_emergency_fund" in weaknesses:
        focus.append(
            "You do not have an emergency fund yet: your first target is one month of basic expenses."
        )
    if "low_savings" in weaknesses:
        focus.append(
            "Your savings level is low: start with 5-10% and increase it when possible."
        )

    # If no critical weakness is detected, focus on optimization.
    if not focus:
        focus.append(
            "No critical weakness was detected. The next step is to optimize and protect what already works."
        )

    return {
        "immediate_actions": block["immediate_actions"],
        "plan_7_days": block["plan_7_days"],
        "plan_30_days": block["plan_30_days"],
        "principles": principles,
        "focus": focus,
    }
