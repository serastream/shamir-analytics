import hashlib
import os
from datetime import datetime

import pandas as pd
import streamlit as st


def _reg_path():
    return st.secrets.get("TELEGRAM_REGISTRY_PATH", "telegram_registry.xlsx")

def _reg_sheet():
    return st.secrets.get("TELEGRAM_REGISTRY_SHEET", "telegram_users")

def _salt():
    return st.secrets.get("TELEGRAM_CODE_SALT", "school_analysis")


def load_registry() -> pd.DataFrame:
    path = _reg_path()
    sheet = _reg_sheet()
    if not os.path.exists(path):
        df = pd.DataFrame(columns=["role","person_id","name","class","code","telegram_username","chat_id","linked_at"])
        save_registry(df)
        return df
    return pd.read_excel(path, sheet_name=sheet)


def save_registry(df: pd.DataFrame) -> None:
    path = _reg_path()
    sheet = _reg_sheet()
    mode = "a" if os.path.exists(path) else "w"
    with pd.ExcelWriter(path, engine="openpyxl", mode=mode, if_sheet_exists="replace") as w:
        df.to_excel(w, sheet_name=sheet, index=False)


def make_code(role: str, person_id: str, ttl_tag: str = "2026") -> str:
    """Детерминированный код: одинаковый для одной персоны (удобно), без хранения “секретов” в коде."""
    raw = f"{role}|{person_id}|{ttl_tag}|{_salt()}"
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10].upper()
    return f"{role[:1].upper()}{ttl_tag}-{person_id}-{h}"


def ensure_person(role: str, person_id: str, name: str, cls: str) -> str:
    """Создаёт/обновляет запись в реестре, возвращает code."""
    df = load_registry()
    person_id = str(person_id)

    code = make_code(role, person_id)

    mask = (df["role"].astype(str) == role) & (df["person_id"].astype(str) == person_id)
    if mask.sum() == 0:
        df.loc[len(df)] = {
            "role": role,
            "person_id": person_id,
            "name": name,
            "class": cls,
            "code": code,
            "telegram_username": None,
            "chat_id": None,
            "linked_at": None,
        }
    else:
        idx = df[mask].index[0]
        df.loc[idx, "name"] = name
        df.loc[idx, "class"] = cls
        df.loc[idx, "code"] = code  # на всякий случай

    save_registry(df)
    return code


def get_chat_id(role: str, person_id: str):
    df = load_registry()
    mask = (df["role"].astype(str) == role) & (df["person_id"].astype(str) == str(person_id))
    if mask.sum() == 0:
        return None
    val = df.loc[df[mask].index[0], "chat_id"]
    return None if pd.isna(val) else int(val)
