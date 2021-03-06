__author__ = 'starcheng'

"""
    resource-clean base on android-resource-remover
    ~~~~~~~~~~

    Implements methods for removing unused android resources based on Android
    Studio Lint results.

    :copyright: (c) 2015 by askk911@163.com
"""

import argparse
import os
import re
import subprocess
from lxml import etree


class Issue:

    """
    Stores a single issue reported by Android Studio Lint scan
    """
    pattern = re.compile('<html>The resource <code>`?([^`]+)`?</code> appears to be unused</html>')

    def __init__(self, filepath, remove_file):
        self.filepath = filepath
        self.remove_file = remove_file
        self.elements = []

    def __str__(self):
        return '{0} {1}'.format(self.filepath, self.elements)

    def __repr__(self):
        return '{0} {1}'.format(self.filepath, self.elements)

    def add_element(self, message):
        res_all = re.findall(Issue.pattern, message)
        if res_all:
            res = res_all[0]
            bits = res.split('.')[-2:]
            self.elements.append((bits[0], bits[1]))
        else:
            print("The pattern '%s' seems to find nothing in the error message '%s'. We can't find the resource and can't remove it. The pattern might have changed, please check and report this in github issues." % (
                Issue.pattern, message))


def parse_args():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--app',
                        help='Path to the Android app. If not specifies it assumes current directory is your Android '
                             'app directory',
                        default='.')
    parser.add_argument('--xml',
                        help='Path to the list result. If not specifies linting will be done by the script',
                        default=None)
    args = parser.parse_args()
    return  args.app, args.xml


def run_lint_command():
    """
    Run lint command in the shell and save results to lint-result.xml
    """
    lint, app_dir, lint_result, ignore_layouts = parse_args()
    if not lint_result:
        lint_result = os.path.join(app_dir, 'lint-result.xml')
        call_result = subprocess.call([lint, app_dir, '--xml', lint_result])
        if call_result > 0:
            print('Running the command failed with result {}. Try running it from the console. Arguments for subprocess.call: {}'.format(
                call_result, [lint, app_dir, '--xml', lint_result]))
    return lint_result, app_dir, ignore_layouts

def is_remove_file(resouce_type):
    """resource type judge for remove """
    if resouce_type == 'anim' or resouce_type == 'drawable' or resouce_type == 'layout':
        return True

    return False

def get_relative_file_path(file_path):
    """get relative file path from lint-result xml file problem item"""
    index = file_path.find('src/')
    if (index > 0):
        return file_path[index:]

    return None

def filter_directory_path(path):
    if path[-1] == '/':
        return path[0:len(path)-1]

    return path

def parse_lint_result(lint_result_path):
    """
    Parse lint-result.xml and create Issue for every problem found
    """
    root = etree.parse(lint_result_path).getroot()
    issues = []
    for issue_xml in root.findall('.//problem'):
        for location in issue_xml.findall('entry_point'):
            filepath = get_relative_file_path(location.get('FQNAME'))
            # if the location contains line and/or column attribute not the entire resource is unused. that's a guess ;)
            # TODO stop guessing
            issue = Issue(filepath, False)
            issue.add_element(issue_xml.find('description').text)
            # type is drawable and anim to delete file
            if is_remove_file(issue.elements[0][0]):
                issue.remove_file = True
            issues.append(issue)
    return issues


def remove_resource_file(issue, filepath):
    """
    Delete a file from the filesystem
    """
    if os.path.exists(filepath):
        print('removing resource: {0}'.format(filepath))
        os.remove(os.path.abspath(filepath))


def remove_resource_value(issue, filepath):
    """
    Read an xml file and remove an element which is unused, then save the file back to the filesystem
    """
    if os.path.exists(filepath):
        for element in issue.elements:
            print('removing {0} from resource {1}'.format(element, filepath))
            parser = etree.XMLParser(remove_blank_text=False, remove_comments=False,
                                     remove_pis=False, strip_cdata=False, resolve_entities=False)
            tree = etree.parse(filepath, parser)
            root = tree.getroot()
            for unused_value in root.findall('.//{0}[@name="{1}"]'.format(element[0], element[1])):
                root.remove(unused_value)
            with open(filepath, 'wb') as resource:
                tree.write(resource, encoding='utf-8', xml_declaration=True)


def remove_unused_resources(issues, app_dir):
    """
    Remove the file or the value inside the file depending if the whole file is unused or not.
    """
    for issue in issues:
        filepath = os.path.join(app_dir, issue.filepath)
        if issue.remove_file:
            remove_resource_file(issue, filepath)
        else:
            remove_resource_value(issue, filepath)


def main():
    app_dir, lint_result_path = parse_args()
    app_dir = filter_directory_path(app_dir)
    issues = parse_lint_result(lint_result_path)
    remove_unused_resources(issues, app_dir)


if __name__ == '__main__':
    main()

