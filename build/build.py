import sys
from pathlib import Path
import base64
import mimetypes

try:
    import yaml
except ImportError:
    print("PyYAML is not installed.\n"
          "Install it using one of these methods:\n\n"
          "Debian-based Linux system:\n"
          "sudo apt install python3-yaml\n\n"
          "Windows/Other:\n"
          "pip install pyyaml")
    sys.exit(1)

try:
    import sass
except ImportError:
    print("libsass is not installed.\n"
          "Install it using one of these methods:\n\n"
          "Debian-based Linux system:\n"
          "sudo apt install python3-libsass\n\n"
          "Windows/Other:\n"
          "pip install libsass")
    sys.exit(1)


def config_error(msg):
    print(f"{msg}\nRefer to the documentation for instructions on how to correctly create a config file.")
    sys.exit(3)


def image_to_data_url(path):
    mimetype, _ = mimetypes.guess_type(path)

    with open(path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("utf-8")

    return f"data:{mimetype};base64,{encoded}"


build_dir_path = Path(__file__).parent
index_path = build_dir_path / "sources" / "index.html"
style_path = build_dir_path / "sources" / "style.scss"
config_path = build_dir_path / "config.yaml"
root_dir = build_dir_path.parent
dist_dir = root_dir / "dist"

# Check source/config files

if not index_path.is_file():
    print(f"Could not find source file {index_path} which is required for building.")
    sys.exit(2)

if not style_path.is_file():
    print(f"Could not find source file {style_path} which is required for building.")
    sys.exit(2)

if not config_path.is_file():
    print(f"Could not find a config file at {config_path} which is required for building.")
    sys.exit(3)

# region Read config
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

if "look" not in config:
    config_error("Key \"look\" not found in config.")

# Get theme files
if "theme" not in config["look"]:
    config_error("Key \"look/theme\" not found in config.")

theme_name = config["look"]["theme"]
theme_dir = root_dir / "themes" / theme_name

if not theme_dir.is_dir():
    print(f"Theme \"{theme_name}\" doesn't exist!\nMake sure there are no typos in the config file or the theme directory name and that the theme exists at {theme_dir}.")
    sys.exit(4)

theme_file_path = theme_dir / f"theme.scss"

if not theme_file_path.is_file():
    print(f"The directory for the \"{theme_name}\" theme exists, but there is no theme.scss file inside it!\nMake sure there is no typo in the name of the file.")
    sys.exit(4)

print(f"Using theme:\n\t{theme_name} ({theme_file_path})")

# Get font files
if "theme" not in config["look"]:
    config_error("Key \"look/theme\" not found in config.")

font_name = config["look"]["font"]
font_dir = root_dir / "fonts" / font_name

if not font_dir.is_dir():
    print(f"Font \"{font_name}\" doesn't exist!\nMake sure there are no typos in the config file or the font directory name and that the font exists at {font_dir}.")
    sys.exit(5)

font_file_path = font_dir / f"font.scss"

if not font_file_path.is_file():
    print(f"The directory for the \"{font_name}\" font exists, but there is no font.scss file inside it!\nMake sure there is no typo in the name of the file.")
    sys.exit(5)

print(f"Using font:\n\t{font_name} ({font_file_path})")

# Get the image file
if "image" not in config["look"]:
    config_error("Key \"look/image\" not found in config.")

image_file_path = Path(config["look"]["image"])

if not image_file_path.is_file():
    print(f"The image specified (\"{image_file_path}\") doesn't exist!\nMake sure there is no typo in the config file or the target image file name.")
    sys.exit(6)

print(f"Using image:\n\t{image_file_path}")

# Get the welcome message
if "message" not in config["look"]:
    config_error("Key \"look/message\" not found in config.")

welcome_message = config["look"]["message"]

print(f"Welcome message:\n\t\"{welcome_message}\"")

# Get the page language and title
if "page" not in config:
    config_error("Key \"page\" not found in config.")

if "lang" not in config["page"]:
    config_error("Key \"page/lang\" not found in config.")

page_language = config["page"]["lang"]

if "title" not in config["page"]:
    config_error("Key \"page/title\" not found in config.")

page_title = config["page"]["title"]

# Get the search settings
if "search" not in config:
    config_error("Key \"search\" not found in config.")

if "placeholder" not in config["search"]:
    config_error("Key \"search/placeholder\" not found in config.")

search_placeholder = config["search"]["placeholder"]
# endregion

# Merge and compile SCSS
with open(theme_file_path, "r") as f:
    style_content = f.read() + "\n"

with open(font_file_path, "r") as f:
    style_content += f.read() + "\n"

with open(style_path, "r") as f:
    style_content += f.read()

try:
    compiled_css = sass.compile(string=style_content, output_style="compressed")
except sass.CompileError as e:
    print("\nFailed to compile your theme/font:")
    print(e)
    sys.exit(7)

# Prepare HTML
if "sections" not in config:
    config_error("Key \"sections\" not found in config.")

if not isinstance(config["sections"], dict):
    config_error("Key \"sections\" exists, but is not the right type (should be a dictionary).")

print("\nGenerating sections...")
sections_html = ""
seperator_counter = 0

for section_name, links in config["sections"].items():
    sections_html += f'<section>\n\t<h3>{section_name}</h3>\n\t<div class="sep"></div>\n\t<ul>\n'

    for link_name, link_data in links.items():
        sections_html += f'\t\t<li data-icon="{link_data["icon"]}"><a href="{link_data["url"]}">{link_name}</a></li>\n'

    sections_html += f'\t</ul>\n</section>\n'

    seperator_counter += 1

    if seperator_counter % 2 == 1:
        sections_html += '<div class="sep"></div>\n'


print("\tSections generated.")

print("\nConverting image...")
image_data_url = image_to_data_url(image_file_path)
print("\tImage converted.")

replacement_map = {
    "LANG": page_language,
    "STYLES": compiled_css,
    "TITLE": page_title,
    "IMAGE": image_data_url,
    "MESSAGE": welcome_message,
    "SECTIONS": sections_html,
    "SEARCH_PLACEHOLDER": search_placeholder
}

with open(index_path, "r") as f:
    index_content = f.read()

for key, value in replacement_map.items():
    index_content = index_content.replace(f"BUILDER:{key}", value)

if not dist_dir.is_dir():
    dist_dir.mkdir()

html_output_file_path = dist_dir / "index.html"

with open(html_output_file_path, "w") as f:
    f.write(index_content)

print(f"\nDone!\n\tCompiled to: {html_output_file_path}")
