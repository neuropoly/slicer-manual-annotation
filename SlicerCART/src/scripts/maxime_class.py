import os
import ast
from collections import defaultdict


def find_class_references(folder_path):
    # Dictionary to store dependencies: {class_name: [list_of_files_that_use_this_class]}
    class_usage = defaultdict(set)
    # Dictionary to map filenames to class names
    class_files = {}

    # Parse each Python file in the directory
    for filename in os.listdir(folder_path):
        if filename.endswith(".py"):
            filepath = os.path.join(folder_path, filename)
            with open(filepath, "r") as file:
                file_content = file.read()

                # Parse the file content to an AST (Abstract Syntax Tree)
                tree = ast.parse(file_content)

                # Find all class definitions in the file and store them in class_files
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_files[node.name] = filename

    # Analyze usage of classes in each file
    for filename in os.listdir(folder_path):
        if filename.endswith(".py"):
            filepath = os.path.join(folder_path, filename)
            with open(filepath, "r") as file:
                file_content = file.read()
                tree = ast.parse(file_content)

                # Check each node in the AST for class references
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name) and node.id in class_files:
                        # Record that filename uses class node.id from another file
                        if class_files[node.id] != filename:
                            class_usage[class_files[node.id]].add(filename)

    # Convert sets to lists for final output
    class_usage = {k: list(v) for k, v in class_usage.items()}
    return class_usage


# # Example usage
folder_path = "/Users/maximebouthillier/gitmax/code/myrepos/test-sma/SlicerCART/src/scripts"
class_usage_dict = find_class_references(folder_path)
# print('class usagfe dict', class_usage_dict)
for element in class_usage_dict:
    print(element, class_usage_dict[element])

