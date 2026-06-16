progress = {"percent": 0}

def hook(d):
    if d["status"] == "downloading":
        percent = d.get("_percent_str", "0%").replace("%", "").strip()
        try:
            progress["percent"] = float(percent)
        except:
            progress["percent"] = 0
    elif d["status"] == "finished":
        progress["percent"] = 100
