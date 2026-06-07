# marketing/views.py
def pricing(request):
    faqs = [
        {
            "q": "Can I cancel anytime?",
            "a": "Yes. You can cancel from the billing page at any time and you "
            "keep access until the end of the current billing period. We do not "
            "charge cancellation fees and we do not prorate partial months.",
        },
        {
            "q": "Do you offer a free trial?",
            "a": "Every plan includes a 14-day free trial with full access to "
            "all features. No credit card is required to start, and we will email "
            "you three days before the trial ends so there are no surprises.",
        },
        {
            "q": "What happens if I exceed my plan limits?",
            "a": "We never cut you off mid-month. If you exceed your plan's "
            "included usage we will notify you and suggest the next tier; "
            "overages are billed at the published per-unit rate.",
        },
        {
            "q": "Can I change plans later?",
            "a": "Absolutely. Upgrades take effect immediately and we prorate the "
            "difference; downgrades take effect at the next billing cycle so you "
            "keep what you have paid for.",
        },
        {
            "q": "Do you offer discounts for annual billing?",
            "a": "Annual billing saves two months versus paying monthly. Nonprofits "
            "and educational institutions qualify for an additional discount — "
            "contact sales for details.",
        },
    ]
    return render(request, "marketing/pricing.html", {"faqs": faqs})
