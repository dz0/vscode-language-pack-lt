#!/usr/bin/python3

import datetime
from glob import glob
import json
import os
from xml.etree import ElementTree

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SOURCE_DIR = os.path.join(REPO_ROOT, 'xliff')
PACKAGE_DIR = os.path.join(REPO_ROOT, 'package')
TRANSLATIONS_DIR = os.path.join(PACKAGE_DIR, 'translations')
EXTENSIONS_DIR = os.path.join(TRANSLATIONS_DIR, 'extensions')

def collect_sources(dir_name):
    pattern = os.path.join(SOURCE_DIR, dir_name, '*.xlf')
    return glob(pattern)

def generate(target_path, input_files, prefix):
    assert len(input_files) > 0
    input_files.sort()
    contents = {}
    for input_file in input_files:
        print("Processing ", input_file)
        tree = ElementTree.parse(input_file)
        root = tree.getroot()
        assert root.tag == '{urn:oasis:names:tc:xliff:document:1.2}xliff'
        for file in root:
            assert file.tag == '{urn:oasis:names:tc:xliff:document:1.2}file'
            if file.get('tool-id') == "crowdin":
                for trans_unit in file.find('{urn:oasis:names:tc:xliff:document:1.2}body'):
                    assert trans_unit.tag == '{urn:oasis:names:tc:xliff:document:1.2}trans-unit'
                    translation = trans_unit.find('{urn:oasis:names:tc:xliff:document:1.2}target')
                    note = trans_unit.find('{urn:oasis:names:tc:xliff:document:1.2}note')
                    assert note.get('from') == 'Crowdin'
                    original_with_id = note.text
                    assert original_with_id.startswith(prefix), (original, prefix)
                    print(original_with_id[len(prefix):].split())
                    (location, id, *_rest) = original_with_id[len(prefix):].split()
                    if location not in contents:
                        contents[location] = {}
                    file_contents = contents[location]
                    if translation is not None:
                        file_contents[id] = translation.text
                    else:
                        source = trans_unit.find('{urn:oasis:names:tc:xliff:document:1.2}source')
                        file_contents[id] = source.text
            else:
                file_contents = {}
                original = file.get('original')
                assert original.startswith(prefix), (original, prefix)
                location = original[len(prefix):]
                for trans_unit in file.find('{urn:oasis:names:tc:xliff:document:1.2}body'):
                    assert trans_unit.tag == '{urn:oasis:names:tc:xliff:document:1.2}trans-unit'
                    translation = trans_unit.find('{urn:oasis:names:tc:xliff:document:1.2}target')
                    id = trans_unit.get('id')
                    assert id not in file_contents
                    if translation is not None:
                        file_contents[id] = translation.text
                    else:
                        source = trans_unit.find('{urn:oasis:names:tc:xliff:document:1.2}source')
                        file_contents[id] = source.text
                assert location not in contents
                contents[location] = file_contents
    data = {
        "": 'Do not edit this file. It is machine generated.',
        "version": "1.0.0",
        "contents": contents,
    }
    with open(target_path, 'w') as fp:
        json.dump(data, fp, indent='\t')

def main():
    assert not os.path.exists(PACKAGE_DIR)
    os.mkdir(PACKAGE_DIR)

    os.mkdir(TRANSLATIONS_DIR)
    generate(
        os.path.join(TRANSLATIONS_DIR, 'main.i18n.json'),
        collect_sources('vscode-editor') + collect_sources('vscode-workbench'),
        'src/'
    )

    os.mkdir(EXTENSIONS_DIR)
    for extension_xfl_path in collect_sources('vscode-extensions'):
        (name, _) = os.path.splitext(os.path.basename(extension_xfl_path))
        generate(
            os.path.join(EXTENSIONS_DIR, name + '.i18n.json'),
            [extension_xfl_path],
            'extensions/{}/'.format(name),
        )

    with open('package.json') as fp:
        package_info = json.load(fp)
#   package_info['version'] = '1.59.{}'.format(
#       datetime.datetime.now().strftime('%Y%m%d%H%M')
#   )
    with open(os.path.join(PACKAGE_DIR, 'package.json'), 'w') as fp:
        json.dump(package_info, fp, indent='\t')

if __name__ == "__main__":
    main()
