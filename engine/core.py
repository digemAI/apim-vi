from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


# Final result structure used by the Streamlit app.
@dataclass
class Result:
    persona: str
    score: int
    resumen: str


# 1) MAIN CLASSIFIER (V1)
def classify (respuestas: Dict[str, Any]) -> Result:
    """
    Applies the base APIM VI rules and returns the user's financial profile.
    """
    score = 0

    # Read input values with safe defaults in case some keys are missing.
    ahorro_pct = respuestas.get("ahorro_mensual_pct", 0)          # 0-50
    compras_imp = respuestas.get("compras_impulsivas_sem", 0)     # 0-14
    registra = respuestas.get("registra_gastos", False)           # bool
    fondo_meses = respuestas.get("fondo_emergencia_meses", 0)     # 0-12

    # Savings: reward saving at least 10%, with an extra bonus at 20% or more.
    if ahorro_pct >= 10:
        score += 3
    if ahorro_pct >= 20:
        score += 2

    # Impulse purchases: penalize frequent emotional spending.
    if compras_imp >= 3:
        score -= 3
    if compras_imp >= 7:
        score -= 2

    # Expense tracking: reward users who track their money flow.
    if registra:
        score += 2

    # Emergency fund: reward 3+ months, with an extra bonus at 6+ months.
    if fondo_meses >= 3:
        score += 3
    if fondo_meses >= 6:
        score += 2

    # Map the score into a financial profile.
    if score <= 0:
        persona = "Impulse Buyer"
        resumen = (
            "You have potential, but money leaves too fast through impulse decisions. "
            "The goal is to control that pattern."
        )
    elif 1 <= score <= 4:
        persona = "Disciplined Saver"
        resumen = (
            "You are building solid habits. With consistency and a few adjustments, "
            "your financial control can improve quickly."
        )
    elif 5 <= score <= 7:
        persona = "Financial Strategist"
        resumen = (
            "You make solid decisions and maintain useful habits. "
            "The next step is turning control into opportunity."
        )
    else:
        persona = "Money Boss"
        resumen = (
            "You show strong control. Now the challenge is to protect, optimize, "
            "and scale what you are already doing well."
        )

    return Result(persona=persona, score=score, resumen=resumen)


# 2) WEAKNESS DETECTOR (V2 helper)
def detectar_debilidades(respuestas: Dict[str, Any]) -> List[str]:
    """
    Detects the user's main financial weaknesses from the input answers.
    """
    weaknesses: List[str] = []

    # Convert values to safe types before applying rules.
    ahorro = int(respuestas.get("ahorro_mensual_pct", 0))                  # %
    impulsivas = int(respuestas.get("compras_impulsivas_sem", 0))          # times/week
    registra = bool(respuestas.get("registra_gastos", False))              # True/False
    fondo = float(respuestas.get("fondo_emergencia_meses", 0))             # months

    # Simple thresholds. These can be adjusted in future versions.
    if impulsivas >= 3:
        weaknesses.append("impulse_spending")

    if not registra:
        weaknesses.append("no_expense_tracking")

    # Treat emergency fund as missing when it covers less than one month.
    if fondo < 1:
        weaknesses.append("no_emergency_fund")

    # Treat savings as low when the user saves less than 10%.
    if ahorro < 10:
        weaknesses.append("low_savings")

    return weaknesses


# 3) RECOMMENDATIONS (V2)
def recomendaciones(persona: str, respuestas: Dict[str, Any]) -> Dict[str, Any]:
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
    weaknesses = detectar_debilidades(respuestas)

    # Recommendations by financial profile.
    por_persona: Dict[str, Dict[str, List[str]]] = {
        "Impulse Buyer": {
            "acciones_inmediatas": [
                "Apply the 48-hour rule: do not buy anything above your limit without waiting two days.",
                "Before buying, ask yourself: 1) Does this make me richer or poorer? 2) Do I really want this, or am I trying to feel better?",
                "Use cash when possible. Paying with physical money makes the decision more visible.",
            ],
            "plan_7_dias": [
                "Day 1: Write down every expense, even if you only use your notes app.",
                "Day 2: Identify three emotional expenses and remove them this week.",
                "Day 3: Set a weekly limit for cravings or non-essential purchases.",
                "Day 4: Apply the 48-hour rule to online carts and impulse purchases.",
                "Day 5: Review your expenses and mark which ones move you closer to or away from your goals.",
                "Day 6: Ask the two spending questions before any non-essential purchase.",
                "Day 7: Review how much you avoided spending by adding friction to impulse decisions.",
            ],
            "plan_30_dias": [
                "Define a fixed savings percentage, starting with at least 10% if possible.",
                "Start building an emergency fund. First target: one month of basic expenses.",
                "Choose one clear goal, such as debt reduction, an emergency fund, or a first investment.",
            ],
        },
        "Disciplined Saver": {
            "acciones_inmediatas": [
                "Formalize the 'pay yourself first' habit: separate at least 10% of your income when it arrives.",
                "Review your expenses and remove one subscription or recurring cost that no longer makes sense.",
                "Write down your main financial goal, such as a three-month emergency fund, a first investment, or debt reduction.",
            ],
            "plan_7_dias": [
                "Day 1: Build a simple overview: income, fixed expenses, and variable expenses.",
                "Day 2: Adjust your savings percentage and define a small amount for fun without guilt.",
                "Day 3: Create or label an account for long-term financial freedom.",
                "Day 4: Identify expensive debt and plan how to reduce it faster.",
                "Day 5: Review whether your expenses reflect what actually matters to you.",
                "Day 6: Set spending limits by category: home, food, transport, and leisure.",
                "Day 7: Review the week and identify the habit that gave you the most control.",
            ],
            "plan_30_dias": [
                "Aim to save between 10% and 20% of your total income when possible.",
                "Reach the first emergency fund milestone: one month of basic expenses.",
                "Learn one financial education concept per week and apply it in a small way.",
            ],
        },
        "Financial Strategist": {
            "acciones_inmediatas": [
                "Write down your target percentages for needs, fun, long-term investing, and financial freedom.",
                "Review fees and taxes from your current financial products and remove anything that drains more than it helps.",
                "Choose one simple investment vehicle and define a monthly amount for it.",
            ],
            "plan_7_dias": [
                "Day 1: Build a personal financial snapshot: assets, liabilities, income, and expenses.",
                "Day 2: Classify expenses into deficit areas and surplus areas.",
                "Day 3: Adjust your budget so monthly surplus becomes intentional.",
                "Day 4: Review the difference between earned income, portfolio income, and passive income.",
                "Day 5: Review whether your decisions support compounding: small improvements repeated over time.",
                "Day 6: Review risks and insurance to protect what you are building.",
                "Day 7: Document what you learned and choose one improvement for next month.",
            ],
            "plan_30_dias": [
                "Consolidate an emergency fund of at least one to three months.",
                "Start or reinforce a diversified long-term investment strategy.",
                "Create a weekly money review habit, such as 20 minutes every Sunday.",
            ],
        },
        "Money Boss": {
            "acciones_inmediatas": [
                "Align your money decisions with your deeper purpose, not only with the number.",
                "Define one major financial objective and two metrics you will monitor.",
                "Document your money flow: what comes in, what goes out, and what builds assets.",
            ],
            "plan_7_dias": [
                "Day 1: Review whether your time is aligned with producing, protecting, budgeting, leveraging, and learning.",
                "Day 2: Ask yourself: am I building assets or only maintaining expensive habits?",
                "Day 3: Adjust your flows so liabilities are supported by assets, not only by salary.",
                "Day 4: Design one additional income system, such as a business, project, or skill.",
                "Day 5: Review your circle: who do you talk to about money, and what mindset do they bring?",
                "Day 6: Adjust your plan based on your energy and reality, not on trends.",
                "Day 7: Review whether your actions move you closer to the life you want, not only the number you want.",
            ],
            "plan_30_dias": [
                "Strengthen at least one real asset: business, real estate, paper assets, or intellectual property.",
                "Define a yearly plan with goals, quarterly milestones, and monthly reviews.",
                "Make financial education a stable habit, not a temporary streak.",
            ],
        },
    }

    # Fall back to Disciplined Saver if an unknown profile arrives.
    bloque = por_persona.get(persona, por_persona["Disciplined Saver"])

    # General APIM principles. These apply to every profile.
    principios: List[str] = [
        "Pay yourself first: reserve part of your income before paying everyone else.",
        "Small good decisions + consistency + time = a radical difference.",
        "Before spending, ask yourself: does this make me richer or poorer? Do I really want it, or am I trying to feel better?",
        "Never make important money decisions from the emotion of the moment.",
        "Use money as a tool for the life you want, not as a measure of your value.",
    ]

    # Personalized focus based on detected weaknesses.
    enfoque: List[str] = []

    if "impulse_spending" in weaknesses:
        enfoque.append(
            "Your weak point is impulse spending: apply the 48-hour rule and ask the two spending questions before buying."
        )
    if "no_expense_tracking" in weaknesses:
        enfoque.append(
            "You are not tracking expenses: seven days of total tracking can make your money flow visible."
        )
    if "no_emergency_fund" in weaknesses:
        enfoque.append(
            "You do not have an emergency fund yet: your first target is one month of basic expenses."
        )
    if "low_savings" in weaknesses:
        enfoque.append(
            "Your savings level is low: start with 5-10% and increase it when possible."
        )

    # If no critical weakness is detected, focus on optimization.
    if not enfoque:
        enfoque.append(
            "No critical weakness was detected. The next step is to optimize and protect what already works."
        )

    return {
        "acciones_inmediatas": bloque["acciones_inmediatas"],
        "plan_7_dias": bloque["plan_7_dias"],
        "plan_30_dias": bloque["plan_30_dias"],
        "principios": principios,
        "enfoque": enfoque,
    }