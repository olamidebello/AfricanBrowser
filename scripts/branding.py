"""Apply a small, auditable branding overlay without renaming code symbols."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

STRING_FILES = (
    "chrome/app/chromium_strings.grd",
    "ios/chrome/app/strings/ios_chromium_strings.grd",
)
LITERAL_CHANGES = {
    "ios/build/chrome_build.gni": ('chromium_short_name = "Chromium"', 'chromium_short_name = "AfricanBrowser"'),
    "chrome/common/chrome_paths_linux.cc": ('std::string data_dir_basename = "chromium";', 'std::string data_dir_basename = "africanbrowser";'),
}


def brand_strings(text):
    # Only text nodes: identifiers, placeholders, descriptions and attribution stay intact.
    ET.fromstring(text)
    def message(match):
        return re.sub(r">([^<]*)<", lambda m: ">" + re.sub(
            r"\bChromium\b", "AfricanBrowser", m.group(1)) + "<", match.group(0))
    result = re.sub(r"<message\b[^>]*>.*?</message>", message, text, flags=re.S)
    ET.fromstring(result)
    return result


def apply(source):
    source = Path(source)
    path = source / "chrome/app/theme/chromium/BRANDING"
    text = path.read_text(encoding="utf-8")
    changes = {
        "COMPANY_FULLNAME": "Olamide Olatayo Bello",
        "COMPANY_SHORTNAME": "AfricanBrowser",
        "PRODUCT_FULLNAME": "AfricanBrowser",
        "PRODUCT_SHORTNAME": "AfricanBrowser",
        "PRODUCT_INSTALLER_FULLNAME": "AfricanBrowser Installer",
        "PRODUCT_INSTALLER_SHORTNAME": "AfricanBrowser Installer",
        "MAC_BUNDLE_ID": "org.africanbrowser.AfricanBrowser",
    }
    for key, value in changes.items():
        text, count = re.subn(r"^" + key + r"=.*$", key + "=" + value, text, flags=re.M)
        if count != 1:
            raise RuntimeError(f"Upstream branding changed: {key}")
    # Validate all required inputs before writing any of them.
    outputs = {path: text}
    for name in STRING_FILES:
        p = source / name
        outputs[p] = brand_strings(p.read_text(encoding="utf-8"))
    for name, (old, new) in LITERAL_CHANGES.items():
        p = source / name
        value = p.read_text(encoding="utf-8")
        if value.count(old) == 1 and new not in value:
            outputs[p] = value.replace(old, new)
        elif value.count(new) == 1 and old not in value:
            outputs[p] = value
        else:
            raise RuntimeError(f"Upstream branding anchor changed: {name}")
    for p, value in outputs.items():
        p.write_text(value, encoding="utf-8")
    return [str(p.relative_to(source)) for p in outputs]
