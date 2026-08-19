from __future__ import annotations

import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account


PAGE_PREFIX = "/states-of-the-industry/"

STATE_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY",
}

st.set_page_config(
    page_title="State by State | Manufacturing Intelligence",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');
      :root { --navy:#073c5b; --blue:#0c6287; --cyan:#39b8c8; --lime:#d6df43; --mist:#edf8f8; --ink:#123246; }
      .stApp { background: linear-gradient(180deg,#f3fbfb 0,#fff 34rem); color:var(--ink); font-family:'DM Sans',sans-serif; }
      [data-testid="stSidebar"] { background:#063a57; color:white; border-right:0; }
      [data-testid="stSidebar"] * { color:white; }
      [data-testid="stSidebar"] [data-baseweb="input"],
      [data-testid="stSidebar"] [data-baseweb="base-input"],
      [data-testid="stSidebar"] [data-baseweb="input"] input,
      [data-testid="stSidebar"] [data-baseweb="base-input"] input,
      [data-testid="stSidebar"] input[type="text"],
      [data-testid="stSidebar"] [data-testid="stDateInput"] input {
        background:#f8ffff !important;
        color:#073c5b !important;
        -webkit-text-fill-color:#073c5b !important;
        opacity:1 !important;
      }
      [data-testid="stSidebar"] [data-testid*="DateInput"],
      [data-testid="stSidebar"] [data-testid*="DateInput"] *,
      [data-testid="stSidebar"] [data-testid*="dateInput"],
      [data-testid="stSidebar"] [data-testid*="dateInput"] * {
        color:#073c5b !important;
        -webkit-text-fill-color:#073c5b !important;
        opacity:1 !important;
        caret-color:#073c5b !important;
      }
      [data-testid="stSidebar"] [data-testid*="DateInput"] svg,
      [data-testid="stSidebar"] [data-testid*="DateInput"] svg *,
      [data-testid="stSidebar"] [data-testid*="dateInput"] svg,
      [data-testid="stSidebar"] [data-testid*="dateInput"] svg * {
        fill:#073c5b !important;
        color:#073c5b !important;
        stroke:#073c5b !important;
      }
      [data-testid="stSidebar"] .stButton button {
        background:var(--lime) !important;
        border:1px solid var(--lime) !important;
        color:var(--navy) !important;
        font-weight:800 !important;
      }
      [data-testid="stSidebar"] .stButton button * {
        color:var(--navy) !important;
        -webkit-text-fill-color:var(--navy) !important;
        opacity:1 !important;
      }
      [data-testid="stSidebar"] .stButton button:hover {
        background:#e4eb62 !important;
        border-color:#e4eb62 !important;
      }
      h1,h2,h3 { font-family:'Manrope',sans-serif !important; letter-spacing:-.035em; color:var(--navy); }
      .block-container { padding-top:1.5rem; max-width:1500px; }
      .hero { background:radial-gradient(circle at 85% 10%,rgba(214,223,67,.85),transparent 19%),linear-gradient(125deg,#073c5b,#08718d); color:white; border-radius:26px; padding:34px 38px 30px; box-shadow:0 22px 60px rgba(7,60,91,.18); margin-bottom:22px; overflow:hidden; position:relative; }
      .hero:after { content:''; position:absolute; right:-40px; bottom:-90px; width:340px; height:210px; border:42px solid rgba(255,255,255,.08); border-radius:50%; transform:rotate(-12deg); }
      .hero-kicker { text-transform:uppercase; letter-spacing:.17em; font-size:.78rem; font-weight:800; color:var(--lime); }
      .hero h1 { color:white; font-size:clamp(2rem,4vw,3.8rem); margin:.2rem 0 .35rem; line-height:1; }
      .hero p { max-width:760px; font-size:1rem; color:#dff7f7; margin:0; }
      .brand-script { font-style:italic; font-weight:600; }
      [data-testid="stMetric"] { background:rgba(255,255,255,.92); border:1px solid #d8ecec; border-radius:18px; padding:16px 18px; box-shadow:0 8px 24px rgba(7,60,91,.07); }
      [data-testid="stMetricLabel"] { color:#5a7584; font-weight:700; }
      [data-testid="stMetricValue"] { color:var(--navy); font-family:'Manrope'; }
      button[data-baseweb="tab"],
      button[data-baseweb="tab"] *,
      [data-testid="stTabs"] [role="tab"],
      [data-testid="stTabs"] [role="tab"] * {
        color:#294f63 !important;
        -webkit-text-fill-color:#294f63 !important;
        opacity:1 !important;
        visibility:visible !important;
        font-weight:800 !important;
      }
      button[data-baseweb="tab"][aria-selected="true"],
      button[data-baseweb="tab"][aria-selected="true"] *,
      [data-testid="stTabs"] [role="tab"][aria-selected="true"],
      [data-testid="stTabs"] [role="tab"][aria-selected="true"] * {
        color:#0c6287 !important;
        -webkit-text-fill-color:#0c6287 !important;
      }
      [data-testid="stSlider"] label,
      [data-testid="stSlider"] label p,
      [data-testid="stSlider"] [data-testid="stWidgetLabel"] p {
        color:#294f63 !important;
        opacity:1 !important;
        font-weight:700 !important;
      }
      [data-testid="stRadio"] label,
      [data-testid="stRadio"] label *,
      [data-testid="stRadio"] p,
      [data-testid="stRadio"] span {
        color:#294f63 !important;
        -webkit-text-fill-color:#294f63 !important;
        opacity:1 !important;
        visibility:visible !important;
        font-weight:700 !important;
      }
      [data-testid="stSelectbox"] label,
      [data-testid="stSelectbox"] label p {
        color:#294f63 !important;
        font-weight:800 !important;
      }
      [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        background:#f4ffff !important;
        border:2px solid #0c7890 !important;
        border-radius:12px !important;
        box-shadow:0 4px 12px rgba(7,60,91,.08) !important;
        min-height:48px !important;
        cursor:pointer !important;
      }
      [data-testid="stSelectbox"] [data-baseweb="select"] > div:hover {
        background:#e8f9f8 !important;
        border-color:#073c5b !important;
      }
      [data-testid="stSelectbox"] [data-baseweb="select"] * {
        color:#073c5b !important;
        -webkit-text-fill-color:#073c5b !important;
        font-weight:700 !important;
        opacity:1 !important;
      }
      [data-testid="stSelectbox"] svg {
        fill:#0c7890 !important;
        color:#0c7890 !important;
      }
      .section-note { color:#68818e; margin-top:-12px; margin-bottom:14px; }
      .chart-heading { color:#073c5b; font-family:'Manrope',sans-serif; font-size:1.08rem; font-weight:800; margin:1rem 0 1.1rem; }
      .sponsor-card { background:linear-gradient(145deg,#fff,#eff9f7); border:1px solid #d5eae7; border-radius:20px; padding:22px; min-height:158px; }
      .sponsor-card .eyebrow { color:#0c7890; font-size:.75rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; }
      .sponsor-card .big { color:#073c5b; font-family:'Manrope'; font-weight:800; font-size:2rem; margin:.25rem 0; }
      .sponsor-card .copy { color:#587480; font-size:.9rem; }
      .status-dot { display:inline-block; width:8px; height:8px; background:#77d16e; border-radius:50%; margin-right:6px; box-shadow:0 0 0 4px rgba(119,209,110,.16); }
      .small-muted { color:#6f8793; font-size:.8rem; }
      .stDataFrame { border:1px solid #dceced; border-radius:14px; overflow:hidden; }
      footer { visibility:hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


def fmt_int(value: float | int) -> str:
    return f"{int(round(value)):,}"


def state_from_path(page_path: str) -> str:
    clean = page_path.split("?")[0]
    parts = [part for part in clean.split("/") if part]
    if len(parts) < 2 or parts[0] != "states-of-the-industry":
        return "Overview"
    return " ".join(part.capitalize() for part in parts[1].split("-"))


def credentials_session() -> AuthorizedSession:
    scopes = ["https://www.googleapis.com/auth/analytics.readonly"]
    credentials = service_account.Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=scopes,
    )
    return AuthorizedSession(credentials)


def gam_session() -> AuthorizedSession:
    scopes = ["https://www.googleapis.com/auth/admanager.readonly"]
    if "gam_service_account" in st.secrets:
        credentials = service_account.Credentials.from_service_account_info(
            dict(st.secrets["gam_service_account"]), scopes=scopes
        )
    else:
        local_key = Path("GAM/advertizerdashboard-acfc4bf4500d.json")
        if not local_key.exists():
            raise RuntimeError("GAM service-account credentials are not configured.")
        credentials = service_account.Credentials.from_service_account_file(local_key, scopes=scopes)
    return AuthorizedSession(credentials)


@st.cache_data(ttl=3600, show_spinner=False)
def load_gam_zeiss() -> tuple[dict[str, Any], pd.DataFrame]:
    session = gam_session()
    network_response = session.get("https://admanager.googleapis.com/v1/networks", timeout=30)
    network_response.raise_for_status()
    networks = network_response.json().get("networks", [])
    if not networks:
        raise RuntimeError("The GAM service account cannot access an Ad Manager network.")
    network = networks[0]
    base = f"https://admanager.googleapis.com/v1/networks/{network['networkCode']}"
    response = session.get(
        f"{base}/lineItems", params={"filter": "Zeiss", "pageSize": 100}, timeout=30
    )
    response.raise_for_status()
    line_items = response.json().get("lineItems", [])
    ad_units: dict[str, str] = {}
    records = []
    for item in line_items:
        targeted = item.get("targeting", {}).get("inventoryTargeting", {}).get("targetedAdUnits", [])
        labels = []
        for target in targeted:
            resource = target.get("adUnit", "")
            if resource and resource not in ad_units:
                unit_response = session.get(f"https://admanager.googleapis.com/v1/{resource}", timeout=30)
                unit_response.raise_for_status()
                unit = unit_response.json()
                ad_units[resource] = unit.get("displayName", unit.get("adUnitCode", resource))
            if resource:
                labels.append(ad_units[resource])
        stats = item.get("stats", {})
        impressions = int(stats.get("impressionsDelivered", 0))
        clicks = int(stats.get("clicksDelivered", 0))
        records.append({
            "Line item": item.get("displayName", "").split(" - 2026 - ")[-1],
            "Order": item.get("orderDisplayName", ""),
            "Start": pd.to_datetime(item.get("startTime")),
            "End": pd.to_datetime(item.get("endTime")),
            "Status": item.get("status", "").replace("_", " ").title(),
            "Type": item.get("lineItemType", "").title(),
            "Targeted inventory": ", ".join(labels) or "Not specified",
            "Impressions": impressions,
            "Clicks": clicks,
            "CTR": clicks / impressions if impressions else 0,
        })
    return network, pd.DataFrame(records)


@st.cache_data(ttl=3600, show_spinner=False)
def discover_property() -> dict[str, str]:
    session = credentials_session()
    response = session.get("https://analyticsadmin.googleapis.com/v1beta/accountSummaries", params={"pageSize": 200})
    response.raise_for_status()
    properties: list[dict[str, str]] = []
    for account in response.json().get("accountSummaries", []):
        for prop in account.get("propertySummaries", []):
            properties.append({
                "id": prop["property"].split("/")[-1],
                "name": prop.get("displayName", prop["property"]),
                "account": account.get("displayName", "Google Analytics"),
            })
    preferred = next((p for p in properties if "advanced manufacturing" in p["name"].lower()), None)
    preferred = preferred or next((p for p in properties if "manufactur" in p["name"].lower()), None)
    if not preferred and properties:
        preferred = properties[0]
    if not preferred:
        raise RuntimeError("The service account cannot access a GA4 property.")
    return preferred


def run_ga_report(property_id: str, start: date, end: date, dimensions: list[str], metrics: list[str]) -> dict[str, Any]:
    session = credentials_session()
    payload: dict[str, Any] = {
        "dateRanges": [{"startDate": start.isoformat(), "endDate": end.isoformat()}],
        "dimensions": [{"name": name} for name in dimensions],
        "metrics": [{"name": name} for name in metrics],
        "dimensionFilter": {
            "filter": {"fieldName": "pagePath", "stringFilter": {"matchType": "BEGINS_WITH", "value": PAGE_PREFIX}}
        },
        "limit": "10000",
    }
    response = session.post(
        f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport",
        json=payload,
    )
    response.raise_for_status()
    return response.json()


def report_frame(report: dict[str, Any]) -> pd.DataFrame:
    dimensions = [header["name"] for header in report.get("dimensionHeaders", [])]
    metrics = [header["name"] for header in report.get("metricHeaders", [])]
    rows = []
    for row in report.get("rows", []):
        item = {name: value.get("value", "") for name, value in zip(dimensions, row.get("dimensionValues", []))}
        item.update({name: float(value.get("value", 0)) for name, value in zip(metrics, row.get("metricValues", []))})
        rows.append(item)
    return pd.DataFrame(rows, columns=dimensions + metrics)


@st.cache_data(ttl=3600, show_spinner=False)
def load_ga4(start: date, end: date) -> tuple[dict[str, str], pd.DataFrame, pd.DataFrame]:
    prop = discover_property()
    metrics = ["activeUsers", "screenPageViews", "sessions", "engagedSessions"]
    pages = run_ga_report(prop["id"], start, end, ["pagePath", "pageTitle"], metrics)
    trend = run_ga_report(prop["id"], start, end, ["date"], metrics)
    page_df = report_frame(pages)
    trend_df = report_frame(trend)
    if not page_df.empty:
        page_df["State"] = page_df["pagePath"].map(state_from_path)
    if not trend_df.empty:
        trend_df["date"] = pd.to_datetime(trend_df["date"], format="%Y%m%d")
    return prop, page_df, trend_df


def meta_get(url: str, token: str) -> dict[str, Any]:
    response = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=3600, show_spinner=False)
def load_meta(start: date) -> tuple[dict[str, Any], pd.DataFrame]:
    token = st.secrets["meta"]["page_access_token"].strip().lstrip("\ufeff")
    page = meta_get("https://graph.facebook.com/v26.0/me?fields=id,name,followers_count", token)
    url = (
        f"https://graph.facebook.com/v26.0/{page['id']}/published_posts"
        "?fields=id,created_time,permalink_url,message,attachments{url},"
        "reactions.limit(0).summary(true),comments.limit(0).summary(true),shares&limit=100"
    )
    posts: list[dict[str, Any]] = []
    cutoff = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
    while url and len(posts) < 500:
        result = meta_get(url, token)
        batch = result.get("data", [])
        posts.extend(batch)
        if batch and datetime.fromisoformat(batch[-1]["created_time"].replace("Z", "+00:00")) < cutoff:
            break
        url = result.get("paging", {}).get("next")

    records = []
    for post in posts:
        attachments = " ".join(a.get("url", "") for a in post.get("attachments", {}).get("data", []))
        searchable = f"{post.get('message', '')} {attachments}"
        if not re.search(r"states-of-the-industry|state by state", searchable, re.I):
            continue
        slug_match = re.search(r"states-of-the-industry/([a-z-]+)", searchable, re.I)
        state = state_from_path(f"{PAGE_PREFIX}{slug_match.group(1)}/") if slug_match else "State by State"
        records.append({
            "State": state,
            "Published": pd.to_datetime(post["created_time"]),
            "Reactions": post.get("reactions", {}).get("summary", {}).get("total_count", 0),
            "Comments": post.get("comments", {}).get("summary", {}).get("total_count", 0),
            "Shares": post.get("shares", {}).get("count", 0),
            "Post": post.get("permalink_url", ""),
        })
    frame = pd.DataFrame(records)
    if not frame.empty:
        frame["Engagements"] = frame[["Reactions", "Comments", "Shares"]].sum(axis=1)
    return page, frame


def instagram_insights(media_id: str, token: str) -> dict[str, int]:
    metrics = "views,reach,total_interactions,likes,comments,saved,shares"
    try:
        result = meta_get(
            f"https://graph.instagram.com/v26.0/{media_id}/insights?metric={metrics}&period=lifetime",
            token,
        )
    except requests.RequestException:
        return {}
    values: dict[str, int] = {}
    for metric in result.get("data", []):
        value = metric.get("values", [{}])[0].get("value", 0)
        values[metric.get("name", "")] = int(value) if isinstance(value, (int, float)) else 0
    return values


@st.cache_data(ttl=3600, show_spinner=False)
def load_instagram(start: date) -> tuple[dict[str, Any], pd.DataFrame]:
    token = st.secrets["instagram"]["access_token"].strip().lstrip("\ufeff")
    account = meta_get(
        "https://graph.instagram.com/v26.0/me?fields=id,user_id,username,name,account_type,media_count,followers_count",
        token,
    )
    result = meta_get(
        "https://graph.instagram.com/v26.0/me/media"
        "?fields=id,caption,media_type,media_product_type,timestamp,permalink,like_count,comments_count"
        "&limit=50",
        token,
    )
    cutoff = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
    media = [
        item for item in result.get("data", [])
        if datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")) >= cutoff
    ]

    state_names = sorted(STATE_ABBR, key=len, reverse=True)
    state_media = []
    for item in media:
        caption = item.get("caption", "")
        state = next((name for name in state_names if re.search(rf"\b{re.escape(name)}\b", caption, re.I)), "")
        campaign = bool(
            re.search(r"state by state|states-of-the-industry", caption, re.I)
            or (state and re.search(r"manufactur", caption, re.I))
        )
        if campaign:
            item["_state"] = state
            state_media.append(item)
    media = state_media

    insight_results: dict[str, dict[str, int]] = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(instagram_insights, item["id"], token): item["id"] for item in media}
        for future in as_completed(futures):
            insight_results[futures[future]] = future.result()

    records = []
    for item in media:
        caption = item.get("caption", "")
        state = item.get("_state", "")
        campaign = True
        insights = insight_results.get(item["id"], {})
        likes = insights.get("likes", item.get("like_count", 0))
        comments = insights.get("comments", item.get("comments_count", 0))
        saves = insights.get("saved", 0)
        shares = insights.get("shares", 0)
        interactions = insights.get("total_interactions", likes + comments + saves + shares)
        records.append({
            "State": state or ("State by State" if campaign else "—"),
            "Campaign": campaign,
            "Published": pd.to_datetime(item["timestamp"]),
            "Type": item.get("media_product_type") or item.get("media_type", "Post"),
            "Views": insights.get("views", 0),
            "Reach": insights.get("reach", 0),
            "Likes": likes,
            "Comments": comments,
            "Saves": saves,
            "Shares": shares,
            "Engagements": interactions,
            "Post": item.get("permalink", ""),
        })
    return account, pd.DataFrame(records)


def aggregate_states(page_df: pd.DataFrame) -> pd.DataFrame:
    if page_df.empty:
        return pd.DataFrame(columns=["State", "Users", "Pageviews", "Sessions", "Engaged Sessions", "Abbr", "Engagement Rate"])
    states = (
        page_df.groupby("State", as_index=False)
        .agg({"activeUsers": "sum", "screenPageViews": "sum", "sessions": "sum", "engagedSessions": "sum"})
        .rename(columns={"activeUsers": "Users", "screenPageViews": "Pageviews", "sessions": "Sessions", "engagedSessions": "Engaged Sessions"})
    )
    states["Abbr"] = states["State"].map(STATE_ABBR)
    states["Engagement Rate"] = states["Engaged Sessions"].div(states["Sessions"].replace(0, pd.NA)).fillna(0)
    return states.sort_values("Pageviews", ascending=False)


with st.sidebar:
    st.markdown("### SME Media")
    st.caption("Manufacturing intelligence dashboard")
    st.divider()
    default_start = date(2024, 5, 15)
    start_date = st.date_input("Start date", value=default_start, max_value=date.today() - timedelta(days=1))
    end_date = st.date_input("End date", value=date.today() - timedelta(days=1), min_value=start_date, max_value=date.today())
    st.caption("GA4 data may take 24–48 hours to finalize.")
    st.divider()
    if st.button("Refresh connected data", width="stretch"):
        st.cache_data.clear()
        st.rerun()

st.markdown(
    """
    <div class="hero">
      <div class="hero-kicker">AdvancedManufacturing.org · Audience Intelligence</div>
      <h1><span class="brand-script">State by State</span></h1>
      <p>A national view of manufacturing readership, state-level momentum, social resonance and sponsor-ready inventory.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    with st.spinner("Connecting to GA4…"):
        property_info, pages, trend = load_ga4(start_date, end_date)
except Exception as exc:
    st.error("The dashboard could not load GA4 data.")
    st.exception(exc)
    st.stop()

meta_error = None
try:
    meta_page, social = load_meta(start_date)
except Exception as exc:
    meta_page = {"name": "Facebook", "followers_count": 0}
    social = pd.DataFrame(columns=["State", "Published", "Reactions", "Comments", "Shares", "Post", "Engagements"])
    meta_error = str(exc)

instagram_error = None
try:
    instagram_account, instagram_social = load_instagram(start_date)
except Exception as exc:
    instagram_account = {"username": "Instagram", "followers_count": 0, "media_count": 0}
    instagram_social = pd.DataFrame(columns=["State", "Campaign", "Published", "Type", "Views", "Reach", "Likes", "Comments", "Saves", "Shares", "Engagements", "Post"])
    instagram_error = str(exc)

states = aggregate_states(pages)
total_users = int(pages["activeUsers"].sum()) if not pages.empty else 0
total_views = int(pages["screenPageViews"].sum()) if not pages.empty else 0
total_sessions = int(pages["sessions"].sum()) if not pages.empty else 0
engaged_sessions = int(pages["engagedSessions"].sum()) if not pages.empty else 0
engagement_rate = engaged_sessions / total_sessions if total_sessions else 0
state_count = int(states["Abbr"].notna().sum()) if not states.empty else 0

st.markdown(
    f"<div class='small-muted'><span class='status-dot'></span>Live connections · {property_info['name']} · {meta_page.get('name', 'Facebook')} · @{instagram_account.get('username', 'Instagram')} · through {end_date.strftime('%b %d, %Y')}</div>",
    unsafe_allow_html=True,
)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Active users", fmt_int(total_users))
k2.metric("Pageviews", fmt_int(total_views), f"{total_views / total_users:.1f} per user" if total_users else None)
k3.metric("Sessions", fmt_int(total_sessions))
k4.metric("Engagement rate", f"{engagement_rate:.1%}")
k5.metric("States with traffic", f"{state_count} / 50")

overview_tab, state_tab, social_tab, zeiss_tab, sponsor_tab = st.tabs([
    "National overview", "State explorer", "Social performance", "Zeiss performance", "Sponsor opportunity"
])

with overview_tab:
    st.subheader("Audience momentum")
    st.markdown("<div class='section-note'>Monthly readership across the State by State hub and every state article.</div>", unsafe_allow_html=True)
    left, right = st.columns([1.45, 1])
    with left:
        if not trend.empty:
            trend_monthly = (
                trend.set_index("date")[["activeUsers", "screenPageViews"]]
                .resample("MS")
                .sum()
                .reset_index()
            )
            trend_monthly["Month"] = trend_monthly["date"].dt.strftime("%b %Y")
            month_order = trend_monthly["Month"].tolist()
            chart_data = trend_monthly[["Month", "screenPageViews", "activeUsers"]].rename(
                columns={"screenPageViews": "Pageviews", "activeUsers": "Active users"}
            ).melt(id_vars="Month", var_name="Metric", value_name="Audience")
            chart_data["Audience"] = chart_data["Audience"].fillna(0)
            fig = px.bar(
                chart_data,
                x="Month",
                y="Audience",
                color="Metric",
                barmode="group",
                category_orders={"Month": month_order, "Metric": ["Pageviews", "Active users"]},
                color_discrete_map={"Pageviews": "#0c6287", "Active users": "#8ccfd2"},
            )
            fig.update_traces(hovertemplate="%{x}<br>%{fullData.name}: %{y:,.0f}<extra></extra>")
            fig.update_layout(
                height=390,
                margin=dict(l=10, r=15, t=55, b=10),
                title=dict(text="Monthly readership", font=dict(color="#073c5b", size=18)),
                barmode="group",
                bargap=.22,
                font=dict(color="#315568", size=13),
                plot_bgcolor="white",
                paper_bgcolor="rgba(0,0,0,0)",
                hovermode="x unified",
                legend=dict(orientation="h", y=1.08, title_text="", font=dict(color="#315568")),
                xaxis=dict(showgrid=False, tickfont=dict(color="#516f7d"), tickangle=-35, automargin=True),
                yaxis=dict(title="Audience", gridcolor="#e1eeee", tickfont=dict(color="#516f7d"), rangemode="tozero"),
                uirevision="monthly-audience-v2",
            )
            st.plotly_chart(
                fig,
                width="stretch",
                config={"displayModeBar": False},
                key=f"monthly-audience-v2-{start_date}-{end_date}",
            )
    with right:
        mapped = states.dropna(subset=["Abbr"])
        if not mapped.empty:
            map_fig = px.choropleth(mapped, locations="Abbr", locationmode="USA-states", color="Pageviews", scope="usa", hover_name="State", hover_data={"Users": ":,.0f", "Pageviews": ":,.0f", "Abbr": False}, color_continuous_scale=[[0, "#dff4f1"], [.5, "#39b8c8"], [1, "#073c5b"]])
            map_fig.update_layout(
                height=390,
                margin=dict(l=0, r=0, t=20, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                coloraxis_colorbar=dict(title="Views", thickness=10),
                dragmode=False,
                geo=dict(scope="usa", projection_type="albers usa"),
            )
            st.plotly_chart(
                map_fig,
                width="stretch",
                config={"displayModeBar": False, "scrollZoom": False, "doubleClick": False},
            )

    st.subheader("State leaderboard")
    leaderboard = states[states["State"].isin(STATE_ABBR)].head(15).copy()
    if not leaderboard.empty:
        leaderboard.insert(0, "Rank", range(1, len(leaderboard) + 1))
        st.dataframe(
            leaderboard[["Rank", "State", "Users", "Pageviews", "Sessions", "Engagement Rate"]],
            hide_index=True,
            width="stretch",
            column_config={
                "Users": st.column_config.NumberColumn(format="localized"),
                "Pageviews": st.column_config.ProgressColumn(format="localized", min_value=0, max_value=max(1, int(leaderboard["Pageviews"].max()))),
                "Sessions": st.column_config.NumberColumn(format="localized"),
                "Engagement Rate": st.column_config.NumberColumn(format="%.1%%"),
            },
        )

with state_tab:
    available_states = states[states["State"].isin(STATE_ABBR)].sort_values("State")["State"].tolist()
    selected_state = st.selectbox("Select a state to explore", available_states, index=available_states.index("Georgia") if "Georgia" in available_states else 0)
    state_row = states[states["State"] == selected_state].iloc[0]
    state_pages = pages[pages["State"] == selected_state].sort_values("screenPageViews", ascending=False)
    st.subheader(f"{selected_state} manufacturing audience")
    a, b, c, d = st.columns(4)
    a.metric("Users", fmt_int(state_row["Users"]))
    b.metric("Pageviews", fmt_int(state_row["Pageviews"]))
    c.metric("Sessions", fmt_int(state_row["Sessions"]))
    d.metric("Engagement rate", f"{state_row['Engagement Rate']:.1%}")
    st.markdown("#### Content performance")
    display_pages = state_pages[["pageTitle", "pagePath", "activeUsers", "screenPageViews", "sessions"]].rename(columns={"pageTitle": "Page", "pagePath": "Path", "activeUsers": "Users", "screenPageViews": "Pageviews", "sessions": "Sessions"})
    display_pages["Path"] = "https://www.advancedmanufacturing.org" + display_pages["Path"]
    st.dataframe(
        display_pages,
        hide_index=True,
        width="stretch",
        column_config={
            "Users": st.column_config.NumberColumn(format="localized"),
            "Pageviews": st.column_config.ProgressColumn(
                format="localized",
                min_value=0,
                max_value=max(1, int(display_pages["Pageviews"].max())),
            ),
            "Sessions": st.column_config.NumberColumn(format="localized"),
            "Path": st.column_config.LinkColumn(display_text="Open article"),
        },
    )

with social_tab:
    st.subheader("Social amplification")
    st.markdown("<div class='section-note'>Connected Facebook and Instagram performance, with State by State campaign posts flagged where identifiable.</div>", unsafe_allow_html=True)
    if meta_error:
        st.warning("Facebook data is temporarily unavailable. Refresh the Meta Page access token in Streamlit Secrets to restore this section.")
    if instagram_error:
        st.warning("Instagram data is temporarily unavailable. Refresh the Instagram access token in Streamlit Secrets to restore this section.")
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("Facebook followers", fmt_int(meta_page.get("followers_count", 0)))
    s2.metric("Instagram followers", fmt_int(instagram_account.get("followers_count", 0)))
    s3.metric("Facebook campaign posts", fmt_int(len(social)))
    s4.metric("Instagram campaign posts", fmt_int(len(instagram_social)))
    total_social_engagements = (social["Engagements"].sum() if not social.empty else 0) + (instagram_social["Engagements"].sum() if not instagram_social.empty else 0)
    s5.metric("Tracked engagements", fmt_int(total_social_engagements))

    platform = st.radio("View platform", ["Facebook", "Instagram"], horizontal=True, label_visibility="collapsed")
    if platform == "Facebook":
        if not social.empty:
            social_chart = social.nlargest(12, "Engagements").sort_values("Engagements").copy()
            social_chart["Post label"] = social_chart.apply(lambda row: f"{row['State']} · {row['Published'].strftime('%b')} {row['Published'].day}", axis=1)
            engagement_mix = social_chart.melt(id_vars=["Post label", "Post", "Published"], value_vars=["Reactions", "Comments", "Shares"], var_name="Engagement type", value_name="Count")
            fig = px.bar(engagement_mix, x="Count", y="Post label", orientation="h", color="Engagement type", barmode="stack", text_auto=True, color_discrete_map={"Reactions": "#0c6287", "Comments": "#39b8c8", "Shares": "#d6df43"})
            fig.update_traces(textposition="inside", textfont=dict(color="white", size=12), hovertemplate="%{y}<br>%{fullData.name}: %{x}<extra></extra>")
            fig.update_layout(height=500, margin=dict(l=10, r=20, t=90, b=20), font=dict(color="#315568", size=13), paper_bgcolor="white", plot_bgcolor="white", legend=dict(orientation="h", x=0, xanchor="left", y=1.12, yanchor="bottom", title_text="", font=dict(color="#315568")), xaxis=dict(title="Engagements", gridcolor="#e1eeee", rangemode="tozero", tickfont=dict(color="#516f7d"), title_font=dict(color="#315568")), yaxis=dict(title="", automargin=True, tickfont=dict(color="#294f63")))
            st.markdown("<div class='chart-heading'>Top Facebook campaign posts</div>", unsafe_allow_html=True)
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key="facebook-engagement-chart")
            st.dataframe(social.sort_values("Engagements", ascending=False), hide_index=True, width="stretch", column_config={"Published": st.column_config.DatetimeColumn(format="MMM D, YYYY"), "Post": st.column_config.LinkColumn(display_text="View on Facebook")})
        else:
            st.info("No matching State by State Facebook posts were identified in this date range.")
    else:
        if not instagram_social.empty:
            ig_chart = instagram_social.copy()
            ig_chart["Mix engagements"] = ig_chart[["Likes", "Comments", "Saves", "Shares"]].sum(axis=1)
            ig_chart = ig_chart.nlargest(12, "Mix engagements").sort_values("Mix engagements")
            ig_chart["Post label"] = ig_chart.apply(lambda row: f"{row['State'] if row['State'] != '—' else row['Type']} · {row['Published'].strftime('%b')} {row['Published'].day}", axis=1)
            ig_mix = ig_chart.melt(id_vars=["Post label", "Post", "Published"], value_vars=["Likes", "Comments", "Saves", "Shares"], var_name="Engagement type", value_name="Count")
            ig_mix = ig_mix[ig_mix["Count"] > 0]
            fig = px.bar(ig_mix, x="Count", y="Post label", orientation="h", color="Engagement type", barmode="stack", text_auto=True, color_discrete_map={"Likes": "#0c6287", "Comments": "#39b8c8", "Saves": "#d6df43", "Shares": "#f3a34a"})
            fig.update_traces(textposition="inside", textfont=dict(color="white", size=12), hovertemplate="%{y}<br>%{fullData.name}: %{x}<extra></extra>")
            fig.update_layout(height=530, margin=dict(l=10, r=20, t=90, b=20), font=dict(color="#315568", size=13), paper_bgcolor="white", plot_bgcolor="white", legend=dict(orientation="h", x=0, xanchor="left", y=1.12, yanchor="bottom", title_text="", font=dict(color="#315568")), xaxis=dict(title="Engagements", gridcolor="#e1eeee", rangemode="tozero", tickfont=dict(color="#516f7d"), title_font=dict(color="#315568")), yaxis=dict(title="", automargin=True, tickfont=dict(color="#294f63")))
            st.markdown("<div class='chart-heading'>Top Instagram posts by engagement mix</div>", unsafe_allow_html=True)
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key="instagram-engagement-chart")
            instagram_table = instagram_social.sort_values("Engagements", ascending=False).copy()
            instagram_table["Campaign"] = instagram_table.apply(
                lambda row: row["State"] if row["Campaign"] and row["State"] != "—" else ("State by State" if row["Campaign"] else "Other content"),
                axis=1,
            )
            instagram_table = instagram_table[["Published", "Type", "Campaign", "Views", "Reach", "Likes", "Comments", "Saves", "Shares", "Engagements", "Post"]]
            st.dataframe(
                instagram_table,
                hide_index=True,
                width="stretch",
                column_config={
                    "Published": st.column_config.DatetimeColumn(format="MMM D, YYYY"),
                    "Views": st.column_config.NumberColumn(format="localized"),
                    "Reach": st.column_config.NumberColumn(format="localized"),
                    "Likes": st.column_config.NumberColumn(format="localized"),
                    "Comments": st.column_config.NumberColumn(format="localized"),
                    "Saves": st.column_config.NumberColumn(format="localized"),
                    "Shares": st.column_config.NumberColumn(format="localized"),
                    "Engagements": st.column_config.NumberColumn(format="localized"),
                    "Post": st.column_config.LinkColumn(display_text="Open post"),
                },
            )
        else:
            st.info("No Instagram posts were available in this date range.")

with zeiss_tab:
    st.subheader("Zeiss display campaign")
    st.markdown(
        "<div class='section-note'>Google Ad Manager delivery for the Zeiss campaign targeted to the State of the Industry inventory.</div>",
        unsafe_allow_html=True,
    )
    try:
        with st.spinner("Loading Zeiss delivery from Google Ad Manager…"):
            gam_network, zeiss_items = load_gam_zeiss()
        if zeiss_items.empty:
            st.info("No Zeiss line items were found in the connected GAM network.")
        else:
            impressions = int(zeiss_items["Impressions"].sum())
            clicks = int(zeiss_items["Clicks"].sum())
            ctr = clicks / impressions if impressions else 0
            campaign_start = zeiss_items["Start"].min()
            campaign_end = zeiss_items["End"].max()
            z1, z2, z3, z4 = st.columns(4)
            z1.metric("Delivered impressions", fmt_int(impressions))
            z2.metric("Ad clicks", fmt_int(clicks))
            z3.metric("Click-through rate", f"{ctr:.2%}")
            z4.metric("Line items", fmt_int(len(zeiss_items)))

            st.markdown(
                f"**Campaign window:** {campaign_start.strftime('%b %d, %Y').replace(' 0', ' ')}–{campaign_end.strftime('%b %d, %Y').replace(' 0', ' ')}  \n"
                f"**GAM network:** {gam_network.get('displayName', gam_network.get('networkCode', 'Google Ad Manager'))}"
            )
            chart = zeiss_items.sort_values("Impressions", ascending=True)
            fig = px.bar(
                chart,
                x="Impressions",
                y="Line item",
                orientation="h",
                text="Impressions",
                color="CTR",
                color_continuous_scale=[[0, "#8ccfd2"], [1, "#0c6287"]],
            )
            fig.update_traces(
                texttemplate="%{x:,.0f}",
                textposition="inside",
                hovertemplate="%{y}<br>Impressions: %{x:,.0f}<br>CTR: %{marker.color:.2%}<extra></extra>",
            )
            fig.update_layout(
                height=350,
                margin=dict(l=10, r=20, t=45, b=20),
                title=dict(text="Delivery by line item", font=dict(color="#073c5b", size=18)),
                paper_bgcolor="white",
                plot_bgcolor="white",
                font=dict(color="#315568"),
                coloraxis_colorbar=dict(title="CTR", tickformat=".2%"),
                xaxis=dict(title="Delivered impressions", gridcolor="#e1eeee"),
                yaxis=dict(title="", automargin=True),
            )
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

            table = zeiss_items[["Line item", "Targeted inventory", "Status", "Start", "End", "Impressions", "Clicks", "CTR"]]
            st.markdown("#### Line-item detail")
            st.dataframe(
                table,
                hide_index=True,
                width="stretch",
                column_config={
                    "Start": st.column_config.DatetimeColumn(format="MMM D, YYYY"),
                    "End": st.column_config.DatetimeColumn(format="MMM D, YYYY"),
                    "Impressions": st.column_config.NumberColumn(format="localized"),
                    "Clicks": st.column_config.NumberColumn(format="localized"),
                    "CTR": st.column_config.NumberColumn(format="%.2%%"),
                },
            )
            st.caption(
                "Impressions, clicks and CTR are live GAM delivery totals. Viewability is omitted because GAM returned no measured viewable impressions for these line items."
            )
    except Exception as exc:
        st.warning("Zeiss GAM reporting is temporarily unavailable.")
        st.exception(exc)

with sponsor_tab:
    st.subheader("Build a monthly sponsorship package")
    st.markdown("<div class='section-note'>Adjust the commercial assumptions to model a recurring, category-exclusive program.</div>", unsafe_allow_html=True)
    monthly = trend.copy()
    if not monthly.empty:
        monthly["Month"] = monthly["date"].dt.to_period("M").astype(str)
        monthly = monthly.groupby("Month", as_index=False)["screenPageViews"].sum()
        avg_monthly_views = float(monthly.tail(6)["screenPageViews"].mean())
    else:
        avg_monthly_views = 0
    control1, control2, control3 = st.columns(3)
    ad_units = control1.slider("Display ad opportunities per pageview", 1.0, 5.0, 2.2, 0.1)
    sell_through = control2.slider("Expected sell-through", 25, 100, 80, 5) / 100
    cpm = control3.slider("Proposed CPM", 10, 75, 30, 1)
    monthly_impressions = avg_monthly_views * ad_units
    billable_impressions = monthly_impressions * sell_through
    media_value = billable_impressions / 1000 * cpm
    cards = st.columns(4)
    values = [
        ("6-month avg. audience", fmt_int(avg_monthly_views), "Monthly State by State pageviews"),
        ("Available inventory", fmt_int(monthly_impressions), "Modeled monthly display impressions"),
        ("Billable inventory", fmt_int(billable_impressions), f"At {sell_through:.0%} sell-through"),
        ("Modeled media value", f"${media_value:,.0f}", f"At a ${cpm} CPM"),
    ]
    for column, (label, value, copy) in zip(cards, values):
        column.markdown(f"<div class='sponsor-card'><div class='eyebrow'>{label}</div><div class='big'>{value}</div><div class='copy'>{copy}</div></div>", unsafe_allow_html=True)
    st.markdown("### Recommended package")
    st.markdown(
        """
        **State by State Presenting Sponsor** — category exclusivity across the national hub and all state articles, premium display placements, sponsor recognition in selected social posts, and a monthly performance recap combining GA4 audience delivery with Facebook engagement.

        Use the modeled media value as the display floor, then add a premium for exclusivity, content association and social amplification. Google Ad Manager delivery and Zeiss benchmarks can be added once those exports or credentials are available.
        """
    )

st.caption(f"Dashboard refreshed {datetime.now().strftime('%b %d, %Y at %I:%M %p')} · GA4 and Meta report aggregated audience data.")
