# State by State Manufacturing Dashboard

An internal Streamlit dashboard for SME Media's **State by State of the Manufacturing Industry** program. It combines GA4 audience analytics, Facebook post performance, state-level content rankings, and adjustable sponsorship forecasting.

## Features

- National audience KPIs and daily traffic trends
- State-by-state U.S. traffic map and leaderboard
- Individual state content explorer
- Facebook reactions, comments, and shares
- Instagram views, reach, interactions, likes, comments, saves, and shares
- Adjustable display inventory, sell-through, and CPM model
- Live GA4 and Meta connections with hourly caching

## Local setup

1. Install Python 3.11 or newer.
2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in the GA4, Facebook, and Instagram credentials. The real secrets file is excluded from Git. Never commit credentials.

4. Ensure the Google Analytics Admin API and Google Analytics Data API are enabled for the service-account project. Add the service account to the GA4 property with Viewer access.

5. Start the dashboard:

   ```powershell
   streamlit run app.py
   ```

The Meta Page token needs `pages_show_list`, `pages_read_engagement`, `pages_read_user_content`, and `read_insights`.
