import os
from collections import defaultdict

def get_folder_paths_by_level(parent_path):
    """
    Returns folder paths grouped by depth level
    """
    grouped = defaultdict(list)

    parent_path = os.path.abspath(parent_path)
    base_depth = parent_path.count(os.sep)

    for root, dirs, files in os.walk(parent_path):
        for d in dirs:
            folder_path = os.path.join(root, d)
            depth = folder_path.count(os.sep) - base_depth
            level = f"level{depth}"
            grouped[level].append(folder_path)

    return dict(grouped)

def get_paths_by_level_and_folder(grouped_paths, level, folder_name):
    """
    grouped_paths: dict -> output of get_folder_paths_by_level()
    level: str -> e.g. 'level2'
    folder_name: str -> e.g. 'D2C', 'Digital POSP'
    """
    if level not in grouped_paths:
        return []

    return [
        path for path in grouped_paths[level]
        if path.endswith(os.sep + folder_name)
    ]



parent_folder = "./Folder_Structure/"
result = get_folder_paths_by_level(parent_folder)

for level, paths in result.items():
    print(level)
    for p in paths:
        print("  ", p)

for level, folders in result.items():
    print(level, ":", folders)