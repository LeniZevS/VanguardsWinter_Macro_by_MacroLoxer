import os
import re
import requests
import zipfile

# This gets the rest of the files and puts them in the right directory.
# This file should be in Utility.
Main_Folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

winter_event_url = "https://raw.githubusercontent.com/loxerex/Winter-Normal-Macro/main/Winter_Event.py"
images_url = "https://github.com/loxerex/Winter-Normal-Macro/raw/refs/heads/main/Images.zip"

winter_event_name = winter_event_url.split("/")[-1].replace(" ", "_")
winter_event_path = os.path.join(Main_Folder, winter_event_name)

images_name = images_url.split("/")[-1].replace(" ", "_")
images_path = os.path.join(Main_Folder, images_name)


def get_cur_ver(target: str = "Winter_Event.py"):
    file_path = os.path.join(Main_Folder, target.lstrip("\\/"))
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as target_file:
        content = target_file.read()
        for line in content.splitlines():
            if "VERSION_N" in line:
                return line
    return None


def get_newest_ver(timeout: int = 20):
    req_obj = requests.get(winter_event_url, timeout=timeout)
    newest_ver = None
    for line in req_obj.text.splitlines():
        if "VERSION_N" in line:
            newest_ver = line
            break
    return newest_ver


def extract_version_number(version_line: str | None):
    if not version_line:
        return None
    match = re.search(r"VERSION_N\s*=\s*['\"]([^'\"]+)['\"]", version_line)
    if match:
        return match.group(1).strip()
    return str(version_line).strip()


def get_version_info(timeout: int = 20, target: str = "Winter_Event.py"):
    current_line = get_cur_ver(target)
    latest_line = None
    error = None
    try:
        latest_line = get_newest_ver(timeout=timeout)
    except Exception as fetch_error:
        error = str(fetch_error)

    return {
        "current_line": current_line,
        "latest_line": latest_line,
        "current_version": extract_version_number(current_line),
        "latest_version": extract_version_number(latest_line),
        "error": error,
    }


def run_file_check(print_fn=print):
    print_fn("Running file check..")
    print_fn(f"Home folder: {Main_Folder}")
    print_fn(f"Winter_Event.py, Exists: {os.path.exists(os.path.join(Main_Folder, 'Winter_Event.py'))}")
    print_fn(f"webhook.py, Exists: {os.path.exists(os.path.join(Main_Folder, 'webhook.py'))}")
    print_fn(f"Position.py, Exists: {os.path.exists(os.path.join(Main_Folder, 'Position.py'))}")

    print_fn(f"Settings Folder: {os.path.join(Main_Folder, 'Settings')}")
    print_fn(
        f"Winter_Event.json, Exists: {os.path.exists(os.path.join(Main_Folder, 'Settings', 'Winter_Event.json'))}"
    )

    print_fn(f"Utility Folder: {os.path.join(Main_Folder, 'Utility')}")
    print_fn(
        f"mouseDebugging.py, Exists: {os.path.exists(os.path.join(Main_Folder, 'Utility', 'mouseDebugging.py'))}"
    )
    print_fn(
        f"SettingsHelper.py, Exists: {os.path.exists(os.path.join(Main_Folder, 'Utility', 'SettingsHelper.py'))}"
    )

    print_fn(f"Tools Folder: {os.path.join(Main_Folder, 'Tools')}")
    print_fn(f"avMethods.py, Exists: {os.path.exists(os.path.join(Main_Folder, 'Tools', 'avMethods.py'))}")
    print_fn(f"botTools.py, Exists: {os.path.exists(os.path.join(Main_Folder, 'Tools', 'botTools.py'))}")
    print_fn(f"winTools.py, Exists: {os.path.exists(os.path.join(Main_Folder, 'Tools', 'winTools.py'))}")

    print_fn(f"Resources Folder, Exists: {os.path.exists(os.path.join(Main_Folder, 'Resources'))}")
    print_fn(f"tesseract Folder, Exists: {os.path.exists(os.path.join(Main_Folder, 'tesseract'))}")


def perform_updates(
    get_winter: bool,
    get_resources: bool,
    timeout: int = 60,
    preserve_local_winter: bool = False,
):
    result = {
        "updated_winter": False,
        "updated_resources": False,
        "skipped_winter": False,
        "error": None,
    }
    try:
        if get_winter:
            if preserve_local_winter and os.path.exists(winter_event_path):
                result["skipped_winter"] = True
            else:
                with requests.get(winter_event_url, stream=True, timeout=timeout) as req:
                    req.raise_for_status()
                    with open(winter_event_path, "wb") as file:
                        for chunk in req.iter_content(chunk_size=8192):
                            file.write(chunk)
                result["updated_winter"] = True

        if get_resources:
            with requests.get(images_url, stream=True, timeout=timeout) as req:
                req.raise_for_status()
                with open(images_path, "wb") as file:
                    for chunk in req.iter_content(chunk_size=8192):
                        file.write(chunk)

            with zipfile.ZipFile(images_path, "r") as archive_file:
                archive_file.extractall(Main_Folder)
            os.remove(images_path)
            result["updated_resources"] = True
    except Exception as error:
        result["error"] = str(error)
    return result


def run_update_flow(
    auto_confirm: bool = False,
    preserve_local_winter: bool = False,
    print_fn=print,
    input_fn=input,
):
    get_winter = False
    get_resources = False
    version_info = get_version_info()
    cur_ver_line = version_info.get("current_line")
    new_ver_line = version_info.get("latest_line")
    cur_ver = version_info.get("current_version")
    new_ver = version_info.get("latest_version")

    result = {
        "updated_winter": False,
        "updated_resources": False,
        "skipped_winter": False,
        "error": None,
        "current_version_line": cur_ver_line,
        "latest_version_line": new_ver_line,
        "current_version": cur_ver,
        "latest_version": new_ver,
        "post_update_version": None,
    }

    if os.path.exists(winter_event_path):
        print_fn("It looks like you already have the files")
        print_fn(f"Current version: {cur_ver or 'unknown'}")
        print_fn(f"Latest version: {new_ver or 'unknown'}")
        if version_info.get("error"):
            print_fn(f"Version check warning: {version_info['error']}")

        if auto_confirm and preserve_local_winter:
            get_winter = False
            get_resources = True
            print_fn("Preserve mode: local Winter_Event.py will not be replaced.")
        else:
            if auto_confirm:
                get_resources = True
                if preserve_local_winter:
                    get_winter = False
                else:
                    # Download Winter_Event.py only when remote version is newer/different.
                    get_winter = (new_ver is None) or (cur_ver != new_ver)
            elif cur_ver == new_ver:
                if auto_confirm:
                    get_winter = True
                    get_resources = True
                else:
                    print_fn("It looks like your winter_event.py is update to date would you like to replace it? [Y/N]")
                    a = input_fn(">")
                    if isinstance(a, str) and a.lower() == "y":
                        get_winter = True

                    print_fn("would you want to update resources? (Y/N)")
                    b = input_fn(">")
                    if isinstance(b, str) and b.lower() == "y":
                        get_resources = True
            else:
                print_fn(f"Your winter_event.py is out of dated! n:{new_ver} | c:{cur_ver}")
                if auto_confirm:
                    get_winter = True
                    get_resources = True
                else:
                    print_fn("Would you like to update? This will also update resources. [Y/N]")
                    a = input_fn(">")
                    if isinstance(a, str) and a.lower() == "y":
                        get_winter = True
                        get_resources = True
    else:
        if auto_confirm:
            get_winter = True
            get_resources = True
        else:
            print_fn("Would you like to download Winter_Event.py and resources? [Y/N]")
            a = input_fn(">")
            if isinstance(a, str) and a.lower() == "y":
                get_winter = True
                get_resources = True

    update_result = perform_updates(
        get_winter=get_winter,
        get_resources=get_resources,
        preserve_local_winter=preserve_local_winter,
    )
    result.update(update_result)
    result["post_update_version"] = extract_version_number(get_cur_ver("Winter_Event.py"))

    if result["error"]:
        print_fn(result["error"])
    elif not get_winter and not get_resources:
        print_fn("No update actions selected.")
    elif get_resources and not get_winter and cur_ver == new_ver:
        print_fn("Winter_Event.py is already up to date. Resources updated.")
    else:
        print_fn("Update finished.")
    return result


def main():
    print("Welcome to the file checker, you can either")
    print("[1] - Run a file check which sees if everything is in the right place")
    print("[2] - Check/update/install winter_event.py + resources")
    try:
        answer = int(input(">"))
    except ValueError:
        print("Invalid option.")
        return

    if answer == 1:
        run_file_check()
    elif answer == 2:
        run_update_flow(auto_confirm=False)
    else:
        print("Invalid option.")


if __name__ == "__main__":
    main()
