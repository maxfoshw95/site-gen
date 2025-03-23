import os
import shutil
import re
import time
import secrets

VER = "4.8"

LOG = True  # Toggle Performance logging
SCOPE = ""  # Scope of the logging
LOGS = []  # List to store logs

components = {}  # List of components
html_files = {}


# Function to store logs
def print_later(string: str, hints: str = "none", sub_function: bool = False):
    if LOG is False:  # Do nothing if logging is turned off
        return

    scope_text = ".child" if sub_function else ".main"

    LOGS.append(
        f"{SCOPE}{scope_text}: {string} {f'| hints: {hints}' if hints != 'none' else ''}"
    )


# Performance logging wrapper
def getperf_wrap(func):
    def wrap(*args, **kwargs):
        start = time.perf_counter_ns()  # start timer
        result = func(*args, **kwargs)

        LOGS.append(
            f" > Performance info for '{func.__name__}': {time.perf_counter_ns() - start} (nanoseconds) \n"
        )
        return result

    return wrap


# A fileIO function for file operation
@getperf_wrap
def fileio(location: str, mode: str, data: str = ""):
    global SCOPE
    SCOPE = "FILEIO"

    location = os.path.normpath(location)  # Normalize the path

    print_later(f"Working with file '{location}', with mode '{mode}'.")
    if os.path.exists(location):
        if mode == "read":
            with open(location, "r", encoding="utf-8") as file:
                return file.read()
        elif mode == "write":
            with open(location, "w", encoding="utf-8") as file:
                file.write(data)
    else:
        raise FileNotFoundError(location)

    return


# Function to format the CSS
@getperf_wrap
def css_format(html_string: str):
    global SCOPE
    SCOPE = "CSS_FORMAT"

    if "<style>" not in html_string:  # Check if there's style element present
        print_later("Exiting due to no CSS element found.", "basic_check")
        return {"html": html_string, "css": ""}

    style_element: str = re.findall(r"<style[^>]*>([\s\S]*?)</style>", html_string)

    if len(style_element) <= 0:
        print_later("Exiting due to no CSS element found.", "regex")
        return {"html": html_string, "css": ""}

    def extract(html_string: str):  # Get CSS class and ID
        return {
            "class": re.findall(r"\.([a-zA-Z0-9_-]+) {", html_string),
            "id": re.findall(r"#([a-zA-Z0-9_-]+) {", html_string),
        }

    # Extract style element
    style_element = style_element[0]

    # Get all CSS data
    css_data = extract(style_element)

    # Remove style element
    html_string = re.sub("<style[^>]*>[\s\S]*?</style>", "", html_string)

    # Random ID
    random_hex = secrets.token_hex(32)

    # Format ID
    for id in css_data["id"]:
        html_string = html_string.replace(f'id="{id}"', f'id="{id}-{random_hex}"')
        style_element = style_element.replace(f"#{id}", f"#{id}-{random_hex}")

    print_later("Finished replacing CSS ID", sub_function=True)

    # Format class
    for sclass in css_data["class"]:
        html_string = re.sub(
            rf'class="([^"]*\b{sclass}\b[^"]*)"',
            f'class="{sclass}-{random_hex}"',
            html_string,
        )
        style_element = style_element.replace(f".{sclass}", f".{sclass}-{random_hex}")

    print_later("Finished replacing CSS Class", sub_function=True)

    print_later(f"Success formatting for id '{random_hex}'")
    return {"html": html_string, "css": style_element}


# Function to format HTML
@getperf_wrap
def html_format(html_string: str):
    global SCOPE
    SCOPE = "HTML_FORMAT"

    formated_string = html_string.replace("\n", "").replace(
        "  ", ""
    )  # Remove newlines and spaces
    print_later("Formatted HTML")

    return formated_string


class main:
    def __init__(
        self,
        components_suffix: str = ".components.html",
        frontend_dir: str = "frontend/",
        build_output_dir: str = "dist/",
    ):
        self.components_suffix = components_suffix
        self.frontend_dir = frontend_dir
        self.build_output_dir = build_output_dir

    @getperf_wrap
    def load_files(self):  # Load components and their HTML and CSS contents
        global SCOPE
        SCOPE = "LOADER"

        for dirpath, _, filenames in os.walk(
            self.build_output_dir
        ):  # Walk all files in the components directory
            for file in filenames:
                filepath = os.path.join(dirpath, file)

                if file.endswith((self.components_suffix, ".html")):
                    output = fileio(filepath, "read")
                    tool_output = css_format(output)

                    if file.endswith(self.components_suffix):
                        data = {
                            f"{file.removesuffix(self.components_suffix)}": {
                                "path": filepath,
                                "html": tool_output.get("html"),
                                "css": tool_output.get("css"),
                                "uid": secrets.token_hex(32),
                            }
                        }

                        components.update(data)

                    elif file.endswith(".html") and not file.endswith(
                        self.components_suffix
                    ):
                        html_files.update(
                            {
                                f"{filepath}": {
                                    "html": tool_output.get("html"),
                                    "css": tool_output.get("css"),
                                }
                            }
                        )
                else:
                    continue

        print_later("Done loading files data")
        return

    @getperf_wrap
    def init_build_dir(self):  # Initialization of the build folder
        global SCOPE
        SCOPE = "MAIN"

        if os.path.exists(self.build_output_dir):
            shutil.rmtree(self.build_output_dir)
        print_later("Removed old directory.", sub_function=True)
        shutil.copytree(self.frontend_dir, self.build_output_dir, dirs_exist_ok=True)
        print_later("Copied build directory.", sub_function=True)
        print_later("Initialized build directory.")

    @getperf_wrap
    def build(self):  # Main function
        global SCOPE
        SCOPE = "MAIN"

        print_later(f"Running YAFB {VER}!\n")

        self.init_build_dir()

        self.load_files()  # Load components and their data

        for html in html_files:
            html_content = html_files.get(html)  # Get HTML output

            file_html = html_content.get("html")

            # Replace all matching component tag
            for component in components:
                file_html = file_html.replace(
                    f":{component};",
                    f"<!-- Begin {components[component]['uid']} -->{components[component]['html']} <!-- End {components[component]['uid']} -->",
                )

                file_html = file_html.replace(
                    "</head>",
                    "<style>" + components[component].get("css") + "</style>\n</head>",
                )

            file_html = file_html.replace(
                "</head>",
                "<style>" + html_content.get("css") + "</style>\n</head>",
            )

            file_html = html_format(file_html)
            fileio(html_files[html].get("path"), "write", file_html)

        SCOPE = "MAIN"
        print_later("Finished building.")

    def print_logs(self):
        if len(LOGS) == 0:
            return

        for log in LOGS:
            print(log)
