# Launch & Monetization Kit: <TITLE> (`<SLUG>`)

## 1. Checkout & License Key Setup (`<PROVIDER>`)
1. Create a new product named **<TITLE> Pro** on `<PROVIDER>` (Polar.sh / Lemon Squeezy / Gumroad).
2. Enable **License Keys** on the product (set activation limit, e.g. 3 devices).
3. Copy your Product ID / Organization ID and Checkout URL.
4. Update:
   - `projects/<SLUG>/launch/landing.html`: replace `#CHECKOUT_URL_HERE`, `<TAGLINE>`, `<PAIN_SUMMARY>`, `<PRO_PRICE>`, and `<HOST_SOFTWARE>`.
   - `projects/<SLUG>/src/` license configuration with your live `productId`.

## 2. Marketplace Listing Draft
- **Title**: <TITLE>
- **Short Summary (<= 132 chars)**: <One-sentence relief statement>
- **Keywords**: <keyword1, keyword2, keyword3>
- **Permissions Justification**: <Minimal permissions used and why>

## 3. "Reply-to-Pain" Sniper Outreach (Non-Spammy)
Use the exact Stage 1 complaint threads below. Only reply where helpful: acknowledge the limitation, explain the fix transparently, and link to the free tier.
- Target Thread 1: <URL>
- Target Thread 2: <URL>

**Reply Template**:
> I ran into this exact limitation in <HOST_SOFTWARE> too. Built a tiny lightweight tool (<TITLE>) that automates <X> without touching your data. Free tier handles <Free Scope> if you want to try it: <URL>. Happy to hear feedback if anything breaks!

## 4. Launch Post Copy (Show HN / Reddit / X)
- **Title**: Show HN: <TITLE> – Fix <Pain> in <HOST_SOFTWARE> in one click
- **Body**:
  - Problem noticed across <N> threads/issues
  - How <TITLE> fixes it locally/cleanly
  - Free tier vs. Pro license model + link to landing page
