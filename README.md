# State by State Manufacturing Dashboard

An internal Streamlit dashboard for SME Media's **State by State of the Manufacturing Industry** program. It combines GA4 audience analytics, Facebook post performance, state-level content rankings, and adjustable sponsorship forecasting.

## Features

- National audience KPIs and daily traffic trends
- State-by-state U.S. traffic map and leaderboard
- Individual state content explorer
- Facebook reactions, comments, and shares
- Adjustable display inventory, sell-through, and CPM model
- Live GA4 and Meta connections with hourly caching

## Local setup

1. Install Python 3.11 or newer.
2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Place the GA4 service-account JSON file and Meta Page token file in the project folder. The default filenames are:

   - `stable-hologram-497015-i9-45282bfa717e.json`
   - `metasecret.txt`

   Both files are excluded from Git. Never commit credentials.

4. Ensure the Google Analytics Admin API and Google Analytics Data API are enabled for the service-account project. Add the service account to the GA4 property with Viewer access.

5. Start the dashboard:

   ```powershell
   streamlit run app.py
   ```

## Optional credential paths

Alternative credential locations can be supplied through environment variables:

```powershell
$env:GA4_SERVICE_ACCOUNT_FILE = "C:\path\to\service-account.json"
$env:META_TOKEN_FILE = "C:\path\to\metasecret.txt"
streamlit run app.py
```

The Meta Page token needs `pages_show_list`, `pages_read_engagement`, `pages_read_user_content`, and `read_insights`.
