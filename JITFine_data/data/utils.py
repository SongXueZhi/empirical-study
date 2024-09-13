import re

TEST_FILES = re.compile(
    r'(^|\/)(test|tests|test_long_running|testing|legacy-tests|testdata|test-framework|derbyTesting|unitTests|java\/stubs|test-lib|src\/it|src-lib-test|src-test|tests-src|test-cactus|test-data|test-deprecated|src_unitTests|test-tools|gateway-test-release-utils|gateway-test-ldap|nifi-mock)\/',
    re.IGNORECASE)
DOCUMENTATION_FILES = re.compile(
    r'(^|\/)(doc|docs|example|examples|sample|samples|demo|tutorial|helloworld|userguide|showcase|SafeDemo)\/',
    re.IGNORECASE)
OTHER_EXCLUSIONS = re.compile(r'(^|\/)(_site|auxiliary-builds|gen-java|external|nifi-external)\/', re.IGNORECASE)
single_comment = r'(?<!:)(?<!")\/\/.*(?<!\>)(?<!\*)(?<!\/)'
multi_comment = r'((\s)*(?<!")(\/\*\*?)(.|\s)*?\*\/)'


def preprocess_code_line(code, remove_python_common_tokens=False):
    code = code.replace('(', ' ').replace(')', ' ').replace('{', ' ').replace('}', ' ').replace('[', ' ').replace(']',
                                                                                                                  ' ').replace(
        '.', ' ').replace(':', ' ').replace(';', ' ').replace(',', ' ').replace(' _ ', '_')
    # java only has " ", """ """
    code = re.sub('``.*``', '<STR>', code)
    code = re.sub("'.*'", '<STR>', code)
    code = re.sub('""".*"""', '<STR>', code)

    code = re.sub('".*"', '<STR>', code)
    code = re.sub('\d+', '<NUM>', code)

    # if remove_python_common_tokens:
    #     new_code = ''
    #
    #     for tok in code.split():
    #         if tok not in python_common_tokens:
    #             new_code = new_code + tok + ' '
    #
    #     return new_code.strip()
    #
    # else:
    #     return code.strip()
    return code.strip()


def split_sentence(sentence):
    sentence = sentence.replace('.', ' . ').replace('_', ' ').replace('@', ' @ ') \
        .replace('-', ' - ').replace('~', ' ~ ').replace('%', ' % ').replace('^', ' ^ ') \
        .replace('&', ' & ').replace('*', ' * ').replace('(', ' ( ').replace(')', ' ) ') \
        .replace('+', ' + ').replace('=', ' = ').replace('{', ' { ').replace('}', ' } ') \
        .replace('|', ' | ').replace('\\', ' \ ').replace('[', ' [ ').replace(']', ' ] ') \
        .replace(':', ' : ').replace(';', ' ; ').replace(',', ' , ').replace('<', ' < ') \
        .replace('>', ' > ').replace('?', ' ? ').replace('/', ' / ')
    sentence = ' '.join(sentence.split())
    return sentence


def preprocess_changes(changes, source_code, lines_no=None):
    # source_code = source_code.replace('ne.setName("**/*");', '<REPLACE>').replace(r'"\/\/.*"', '<REPLACE>')
    # print(source_code)
    # source_code = re.sub(multi_comment, '', source_code)
    # print(source_code)
    #
    # source_code = re.sub(single_comment, '', source_code)
    # print(source_code)
    # source_code = [line.strip() for line in source_code.replace('\r').split('\n')]
    changes = check_change_line(changes, lines_no)
    if lines_no is None:
        changes = [line.replace(r'\\r', '').replace(r'\\t', '').replace(r'\r',
                                                                        '').replace(
            r'\t', '').strip() for line in changes if line in source_code and len(line)]
    else:
        changes = [(no, line.replace(r'\\r', '').replace(r'\\t', '').replace(r'\r',
                                                                             '').replace(
            r'\t', '').strip()) for no, line in changes if line in source_code and len(line)]
    # source_code = source_code.replace('<REPLACE>', 'ne.setName("**/*");')

    # print(source_code)
    return changes


def check_change_line(lines, lines_no=None):
    if lines_no is None:
        changes = [re.sub(single_comment, '', l).strip() for l in lines]
    else:
        changes = [(no, re.sub(single_comment, '', l).strip()) for no, l in zip(lines_no, lines)]

    return changes


def java_filename_filter(filename, production_only=False):
    """
    cheks if a file is a java file
    :param filename: name of the file
    :param production_only: if True, the function excludes tests and documentation, eg. test and example folders
    :return: True if the file is java, false otherwise
    """
    ret = filename.endswith('.java') and \
          not filename.endswith('package-info.java')
    if production_only:
        ret = ret and \
              not re.search(TEST_FILES, filename) and \
              not re.search(DOCUMENTATION_FILES, filename) and \
              not re.search(OTHER_EXCLUSIONS, filename)
    return ret


def check_line(lines, line_number):
    """This function tries to extract the complete bug line
    when it is expanded on multiple lines or the line number
    in the dataset is pointing to somewhere else like comments
    before reaching the actual line, etc.
    """
    new_lines = list()
    # print(type(lines))
    # print(line_number, len(lines))
    # print('total lines:', len(lines))
    if line_number >= len(lines):
        return lines
    # Regex patterns for single and multiline comments
    # single_comment = r'(?<!:)\/\/.*(?<!\>)'
    # multi_comment = r'\/\*(.|\s)*?\*\/'

    while line_number < len(lines):
        target_line = lines[line_number].strip()
        # print(line_number, len(lines), target_line)

        # First multiline, then single line to avoid `/* // */`
        # stripped_line = re.sub(multi_comment, '', target_line).strip()
        stripped_line = re.sub(single_comment, '', target_line).strip()
        # The given line is a multiline comment
        if stripped_line.strip().startswith('/*'):
            while '*/' not in lines[line_number].strip() and line_number < len(lines) - 1:
                # print('a', line_number, len(lines), lines[line_number])
                # del lines[line_number]
                line_number += 1
            line_number += 1
            # del lines[line_number]
        else:
            # lines[line_number] = stripped_line
            new_lines.append(stripped_line.strip())
            # print('b', line_number, len(lines), lines[line_number])
            line_number += 1
            # print('b', line_number, len(lines), line_number < len(lines))
    # print('abc')
    # return check_line(lines, line_number + 1)
    new_lines = list(filter(lambda x: len(x), new_lines))
    return new_lines
