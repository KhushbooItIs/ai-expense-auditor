# Metrics

## North Star metric

**Credex consultations booked per week**

This is the only metric that directly measures whether the tool is working as a lead-gen funnel. Audits completed matters, but an audit that doesn't route to a consult booking is just a free calculator. Email captures matter, but they're a proxy. The consult booking is where Credex's business begins.

Why not "audits completed"? Because someone can run 10,000 audits on tiny solo accounts with $20/mo spend and generate zero Credex leads. Volume without qualification is noise.

---

## 3 input metrics that drive the North Star

### 1. High-savings audit rate
**Definition:** % of completed audits where `route == "high_savings"` (savings ≥ $500/mo)

Why it matters: Only high-savings audits show the Credex CTA. If this rate is low, the top of the funnel is full of small accounts that can't convert. Target: ≥15% of completed audits.

If low: distribution is reaching the wrong audience (solo devs instead of team leads). Fix: narrow targeting to Engineering Managers and CTOs at 10+ person companies.

### 2. Audit completion rate
**Definition:** % of visitors who land on `/` and reach a result page

Why it matters: This measures whether the form is clear and the value proposition is compelling enough to get someone through a 2-minute data-entry task. Target: ≥55%.

If low: form is too long, confusing, or visitors don't trust the tool. Fix: reduce friction (pre-fill example values, add a "sample audit" button), improve the hero copy.

### 3. Email capture rate (of high-savings completions)
**Definition:** % of high-savings result pages where a Lead is created

Why it matters: This is the hand-raise signal. A high-savings result that doesn't capture an email is a qualified lead that walked out the door. Target: ≥20% of high-savings results.

If low: the email ask is appearing at the wrong moment or the copy isn't compelling. Fix: A/B test the email gate position and copy.

---

## What to instrument first

1. **Audit completion events** — log `Audit.created_at` with `route` and `total_current_spend`. This gives the pipeline view: volume, qualification rate, and spend distribution in one query.

2. **Lead capture events** — log `Lead.created_at` linked to audit route and monthly_savings. This shows funnel conversion.

3. **Consult CTA clicks** — add a `click` log when the Credex "Book a consult" link is clicked on high-savings result pages. This is the step between "saw the CTA" and "booked a call" — the gap here tells us whether copy or the Credex landing page is the bottleneck.

4. **Share link copies** — track when users click "Copy share link." This measures virality potential before it materialises as inbound traffic.

---

## What number triggers a pivot decision

**If, after 500 completed audits:**
- High-savings audit rate < 8% → audience is wrong; revisit distribution channels
- Consult booking rate < 0.5% of all audits → Credex CTA or landing page isn't converting; A/B test or change the offer
- Email capture rate < 5% of all completions → value proposition isn't landing; revisit result page design

**The pivot signal:** If after 1,000 audits the tool generates zero Credex consultation bookings, the problem is one of three things: wrong audience, wrong CTA, or the savings amounts aren't big enough to motivate action. Each has a different fix. Measure all three separately before deciding.
