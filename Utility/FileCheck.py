import os
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


def run_file_check(print_fn=print):
    print_fn("Running file check..")
    print_fn(f"Home folder: {Main_Folder}")
    print_fn(f"Winter_Event.py, Exists: {os.path.exists(os.path.join(Main_Folder, 'Winter_Event.py'))}")
    print_fn(f"webhook.py, Exists: {os.path.exists(os.path.join(Main_Folder, 'webhook.py'))}")
    print_fn(f"Position.py, Exists: {os.path.exists(os.path.join(Main_Folder, 'Position.py'))}")

    print_fn(f"Settings Folder: {os.path.join(Main_Folder, 'Settings')}")
    print_fn(
        f"Winter_Event.json, Exists: {os.path.exists(os.path.join(Main_Folder, 'Settings\\Winter_Event.json'))}"
    )

    print_fn(f"Utility Folder: {os.path.join(Main_Folder, 'Utility')}")
    print_fn(
        f"mouseDebugging.py, Exists: {os.path.exists(os.path.join(Main_Folder, 'Utility\\mouseDebugging.py'))}"
    )
    print_fn(
        f"SettingsHelper.py, Exists: {os.path.exists(os.path.join(Main_Folder, 'Utility\\SettingsHelper.py'))}"
    )

    print_fn(f"Tools Folder: {os.path.join(Main_Folder, 'Tools')}")
    print_fn(f"avMethods.py, Exists: {os.path.exists(os.path.join(Main_Folder, 'Tools\\avMethods.py'))}")
    print_fn(f"botTools.py, Exists: {os.path.exists(os.path.join(Main_Folder, 'Tools\\botTools.py'))}")
    print_fn(f"winTools.py, Exists: {os.path.exists(os.path.join(Main_Folder, 'Tools\\winTools.py'))}")

    print_fn(f"Resources Folder, Exists: {os.path.exists(os.path.join(Main_Folder, 'Resources'))}")
    print_fn(f"tesseract Folder, Exists: {os.path.exists(os.path.join(Main_Folder, 'tesseract'))}")


def perform_updates(get_winter: bool, get_resources: bool, timeout: int = 60):
    result = {
        "updated_winter": False,
        "updated_resources": False,
        "error": None,
    }
    try:
        if get_winter:
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


def run_update_flow(auto_confirm: bool = False, print_fn=print, input_fn=input):
    get_winter = False
    get_resources = False

    if os.path.exists(winter_event_path):
        print_fn("It looks like you already have the files")
        cur_ver = get_cur_ver("Winter_Event.py")
        new_ver = get_newest_ver()

        if cur_ver == new_ver:
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

    result = perform_updates(get_winter=get_winter, get_resources=get_resources)
    if result["error"]:
        print_fn(result["error"])
    elif not get_winter and not get_resources:
        print_fn("No update actions selected.")
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
