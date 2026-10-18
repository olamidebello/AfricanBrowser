"""Apply a small, auditable branding overlay without renaming code symbols."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

STRING_FILES = (
    "chrome/app/chromium_strings.grd",
    "ios/chrome/app/strings/ios_chromium_strings.grd",
)
ANDROID_NAME_FILE = "chrome/android/java/res_chromium_base/values/channel_constants.xml"

DEFAULT_HOMEPAGE = "https://africanbrowser.com/"
LITERAL_CHANGES = {
    "chrome/browser/profiles/profile_impl.cc": (
        'registry->RegisterStringPref(prefs::kHomePage, std::string(),',
        f'registry->RegisterStringPref(prefs::kHomePage, "{DEFAULT_HOMEPAGE}",'),
    "chrome/browser/ui/browser_ui_prefs.cc": (
        'registry->RegisterBooleanPref(prefs::kHomePageIsNewTabPage, true,',
        'registry->RegisterBooleanPref(prefs::kHomePageIsNewTabPage, false,'),
    "chrome/android/java/src/org/chromium/chrome/browser/homepage/HomepageManager.java": (
        'return getNtpUrl(isIncognito);\n    }\n\n    /**\n     * Determines',
        f'return isIncognito ? getNtpUrl(true) : new GURL("{DEFAULT_HOMEPAGE}");'
        '\n    }\n\n    /**\n     * Determines'),
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


def brand_android_names(text):
    root = ET.fromstring(text)
    required = {"app_name", "bookmark_widget_title", "search_widget_title",
                "quick_action_search_widget_title"}
    for name in required:
        nodes = root.findall(f"string[@name='{name}']")
        if len(nodes) != 1 or not nodes[0].text or not re.search(
                r"\b(?:Chromium|AfricanBrowser)\b", nodes[0].text):
            raise RuntimeError(f"Upstream Android name changed: {name}")
    # Preserve comments, copyright and XML attributes verbatim.
    result = re.sub(r"(<string\b[^>]*>)([^<]*)(</string>)",
                    lambda m: m[1] + re.sub(r"\bChromium\b", "AfricanBrowser", m[2]) + m[3],
                    text)
    # The launcher label must be exact even if upstream adds a channel suffix.
    result = re.sub(r'(<string\b[^>]*\bname=[\'"]app_name[\'"][^>]*>)[^<]*(</string>)',
                    lambda m: m[1] + 'AfricanBrowser' + m[2], result)
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
    android_names = source / ANDROID_NAME_FILE
    outputs[android_names] = brand_android_names(android_names.read_text(encoding="utf-8"))
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
