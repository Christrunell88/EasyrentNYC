# Google Analytics Setup Guide - NoFeesApts.com

## Step 1: Create Google Analytics Account

1. Go to [Google Analytics](https://analytics.google.com)
2. Click "Start measuring"
3. Create Account: "NoFeesApts"
4. Create Property: "NoFeesApts.com"
5. Select Industry: Real Estate
6. Business Size: Small
7. Data Sharing Settings: Enable all recommended

## Step 2: Get Your Measurement ID

1. After property creation, you'll see your **Measurement ID** (format: G-XXXXXXXXXX)
2. Copy this ID

## Step 3: Update Your Website

Replace `G-XXXXXXXXXX` in `/app/frontend/public/index.html` with your actual Measurement ID.

The code is already installed at line 115. Just replace the placeholder.

## Step 4: Set Up Enhanced Tracking

### Recommended Events to Track:

**User Engagement:**
- `sign_up` - When user creates account
- `login` - When user logs in
- `search` - When user filters apartments
- `view_apartment` - When user views apartment details
- `save_favorite` - When user saves apartment to favorites
- `contact_building` - When user clicks contact info

**Example Implementation:**
```javascript
// In your React components
window.trackEvent('sign_up', {
  method: 'email',
  page: 'landing'
});

window.trackEvent('search', {
  bedrooms: '1',
  city: 'Manhattan',
  price_range: '2000-3000'
});
```

## Step 5: Set Up Conversions

In Google Analytics:
1. Go to "Events"
2. Mark these as conversions:
   - `sign_up` (Primary)
   - `contact_building` (Secondary)
   - `save_favorite` (Engagement)

## Step 6: Set Up Audiences

Create these audiences for remarketing:
1. **Active Apartment Seekers** - Viewed 3+ apartments
2. **Manhattan Seekers** - Searched Manhattan apartments
3. **Budget Conscious** - Filtered by price under $3000
4. **Studio Seekers** - Searched studio apartments

## Key Metrics to Monitor

### Traffic Metrics:
- Total Users
- New Users
- Sessions
- Pageviews
- Bounce Rate
- Average Session Duration

### Engagement Metrics:
- Pages per Session
- Event Count
- Conversion Rate

### Acquisition:
- Organic Search (goal: 60%+)
- Direct Traffic
- Social Traffic
- Referral Traffic

## Custom Reports to Create

1. **Apartment Search Report**
   - Dimension: City, Bedrooms, Price Range
   - Metrics: Searches, Conversion Rate

2. **User Journey Report**
   - Landing Page → Sign Up → Search → View → Contact

3. **Location Performance**
   - Which neighborhoods drive most traffic
   - Which have highest conversion rates

## Integration with Google Search Console

Link your Search Console account to see:
- Search queries bringing users
- Click-through rates
- Average position
- Impressions

## Privacy & GDPR Compliance

Analytics is configured with:
- ✅ IP Anonymization enabled
- ✅ No personally identifiable information collected
- ✅ Cookie consent (add banner if needed)

## Testing Your Setup

1. Visit your site in incognito mode
2. Check real-time reports in GA (Reports → Realtime)
3. Trigger some events (sign up, search)
4. Verify events appear in real-time view

## Advanced: Google Tag Manager (Optional)

For easier event tracking without code changes:
1. Create GTM account
2. Install GTM container
3. Set up tags for events
4. Deploy changes through GTM interface

## Expected Results Timeline

- **Day 1:** Real-time data available
- **Week 1:** Traffic patterns emerge
- **Month 1:** Enough data for optimization decisions
- **Month 3:** Full seasonal understanding

## Contact for Help
Email: placesfirm@gmail.com
Phone: 646-408-8048
