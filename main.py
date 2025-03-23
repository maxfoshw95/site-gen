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
        return {"html": html_string, "style": ""}

    style_element: str = re.findall(r"<style[^>]*>([\s\S]*?)</style>", html_string)

    if len(style_element) <= 0:
        print_later("Exiting due to no CSS element found.", "regex")
        return {"html": html_string, "style": ""}

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
    return {"html": html_string, "style": style_element}


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

        HTML = []
        
        for dirpath, _, filenames in os.walk(
            self.build_output_dir
        ):  # Walk all files in the components directory
            for file in filenames:
                if file.endswith(
                    self.components_suffix
                ):  # if it ends with the component suffix
                    full_path = os.path.join(dirpath, file)
                    print_later(
                        f"Found component '{file.removesuffix(self.components_suffix)}'",
                        sub_function=True,
                    )
                    components.update(
                        {
                            f"{file.removesuffix(self.components_suffix)}": {
                                "path": full_path,
                                "html": "",
                                "css": "",
                            }
                        }
                    )
                elif file.endswith(".html") and not file.endswith(self.components_suffix):
                    HTML.append(os.path.join(dirpath, file))
                
        for component in components:  # Process all components
            output = fileio(components[component]["path"], "read")  # Read the component
            tool_output = css_format(output)
            components[component]["html"] = tool_output.get(
                "html"
            )  # Set the component HTML
            components[component]["css"] = tool_output.get("style")  # Set CSS
            components[component]["uid"] = secrets.token_hex(32)  # Generate a random ID

        print_later("Done loading components's HTML and CSS.")
        return HTML

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

        html_files = self.load_files()  # Load components and their data

        for html in html_files:
            html_content = fileio(html, "read")  # Read the HTML

            format_output = css_format(html_content)  # Format the CSS

            html_content = format_output.get("html")  # Get HTML output

            # Replace all matching component tag
            for component in components:
                html_content = html_content.replace(
                    f":{component};",
                    f"<!-- Begin {components[component]['uid']} -->{components[component]['html']} <!-- End {components[component]['uid']} -->",
                )

                html_content = html_content.replace(
                    "</head>",
                    "<style>" + components[component]["css"] + "</style>\n</head>",
                )

            html_content = html_content.replace(
                "</head>",
                "<style>" + format_output.get("style") + "</style>\n</head>",
            )

            html_content = html_format(html_content)
            fileio(html, "write", html_content)

        SCOPE = "MAIN"
        print_later("Finished building.")
        
    
    def print_logs(self):
        if len(LOGS) == 0:
            return
        
        for log in LOGS:
            print(log)
