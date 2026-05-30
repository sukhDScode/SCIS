import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json

# ── INITIALISE FIREBASE (only once) ──────────────────────────────────────────
if not firebase_admin._apps:
    try:
        import streamlit as st
        key_dict = json.loads(st.secrets["firebase"]["service_account_key"])
        cred = credentials.Certificate(key_dict)
    except Exception:
        # Fallback for local development
        cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()


# ─────────────────────────────────────────────────────────────────────────────
#  SAVE FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def save_login(username: str, email: str = ""):
    try:
        db.collection("activity_log").add({
            "username":  username,
            "email":     email,
            "action":    "login",
            "timestamp": datetime.utcnow(),
        })
        print(f"[Firebase] OK  Login saved for: {username}")
    except Exception as e:
        print(f"[Firebase] ERR save_login failed: {e}")


def save_placement_prediction(username: str, inputs: dict,
                               result_pct: float, verdict: str,
                               salary: str = ""):
    try:
        db.collection("placement_predictions").add({
            "username":   username,
            "inputs":     inputs,
            "result_pct": result_pct,
            "verdict":    verdict,
            "salary":     salary,
            "timestamp":  datetime.utcnow(),
        })
        print(f"[Firebase] OK  Prediction saved for: {username}")
    except Exception as e:
        print(f"[Firebase] ERR save_placement_prediction failed: {e}")


def save_recommendation(username: str, inputs: dict,
                         result_pct: float, recommendations: list):
    try:
        db.collection("recommendations").add({
            "username":        username,
            "inputs":          inputs,
            "result_pct":      result_pct,
            "recommendations": recommendations,
            "timestamp":       datetime.utcnow(),
        })
        print(f"[Firebase] OK  Recommendation saved for: {username}")
    except Exception as e:
        print(f"[Firebase] ERR save_recommendation failed: {e}")


def save_resume_analysis(username: str, job_role: str, score: float,
                          found: list, missing: list, missing_adv: list):
    try:
        db.collection("resume_analyses").add({
            "username":    username,
            "job_role":    job_role,
            "score":       score,
            "found":       found,
            "missing":     missing,
            "missing_adv": missing_adv,
            "timestamp":   datetime.utcnow(),
        })
        print(f"[Firebase] OK  Resume analysis saved for: {username}")
    except Exception as e:
        print(f"[Firebase] ERR save_resume_analysis failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
#  FETCH FUNCTIONS
#  Sorting done in Python — avoids needing Firestore composite indexes.
# ─────────────────────────────────────────────────────────────────────────────

def _sort(docs: list, limit: int) -> list:
    import datetime as dt
    def get_ts(d):
        ts = d.get("timestamp")
        if ts is None:
            return dt.datetime.min
        if hasattr(ts, 'seconds'):
            return dt.datetime(1970,1,1) + dt.timedelta(seconds=ts.seconds)
        return ts
    return sorted(docs, key=get_ts, reverse=True)[:limit]


def fetch_activity_log(username: str, limit: int = 20) -> list:
    try:
        docs = db.collection("activity_log").where("username","==",username).stream()
        return _sort([d.to_dict() for d in docs], limit)
    except Exception as e:
        print(f"[Firebase] ERR fetch_activity_log: {e}")
        return []


def fetch_placement_history(username: str, limit: int = 10) -> list:
    try:
        docs = db.collection("placement_predictions").where("username","==",username).stream()
        return _sort([d.to_dict() for d in docs], limit)
    except Exception as e:
        print(f"[Firebase] ERR fetch_placement_history: {e}")
        return []


def fetch_recommendation_history(username: str, limit: int = 10) -> list:
    try:
        docs = db.collection("recommendations").where("username","==",username).stream()
        return _sort([d.to_dict() for d in docs], limit)
    except Exception as e:
        print(f"[Firebase] ERR fetch_recommendation_history: {e}")
        return []


def fetch_resume_history(username: str, limit: int = 10) -> list:
    try:
        docs = db.collection("resume_analyses").where("username","==",username).stream()
        return _sort([d.to_dict() for d in docs], limit)
    except Exception as e:
        print(f"[Firebase] ERR fetch_resume_history: {e}")
        return []


def fetch_student_summary(username: str) -> dict:
    logins      = fetch_activity_log(username, limit=100)
    predictions = fetch_placement_history(username, limit=100)
    resumes     = fetch_resume_history(username, limit=100)
    return {
        "total_logins":          len(logins),
        "total_predictions":     len(predictions),
        "total_resume_analyses": len(resumes),
        "last_prediction":       predictions[0] if predictions else None,
        "last_resume":           resumes[0]     if resumes     else None,
    }
