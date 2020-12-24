import os
import subprocess
import platform
from packaging import version
import json
import sys
import re
import termcolor


def print_warning(msg):
    termcolor.cprint(msg, 'yellow')


def print_critical(msg):
    termcolor.cprint(msg, 'red')


def print_success(msg):
    termcolor.cprint(msg, 'green')


def read_list_from_file(path):
    try:
        with open(path, 'r') as fp:
            list_obj = fp.read().splitlines()
        return list_obj
    except FileNotFoundError as e:
        raise e


def write_list_to_file(list_object, path):
    with open(path, "w") as f:
        f.write("\n".join(str(item) for item in list_object))


def get_db(path='../db/vulndb_full.json'):
    with open(path, 'r') as fp:
        insecure_full = json.load(fp)
    return insecure_full


ops = {
    '==': lambda x, y: version.parse(x) == version.parse(y),
    '<=': lambda x, y: version.parse(x) <= version.parse(y),
    '>=': lambda x, y: version.parse(x) >= version.parse(y),
    '<': lambda x, y: version.parse(x) < version.parse(y),
    '>': lambda x, y: version.parse(x) > version.parse(y),
}


def operand_parse(package_name, regex="(^[\w*\-*]+)*\s*([<>=]+)*\s*(\d+.*)*\s*"):
    """
    A method that parse package name formatted as 'pname==2.2.3' with regex
    :param package_name:
    :param regex:
    :return:
    """
    pattern = re.compile(regex)
    return pattern.match(package_name).groups()


def check_package(package, allowed_operands, regex="(^[\w*\-*]+)*\s*([<>=]+)*\s*(\d+.*)*\s*"):
    """
    A method that preprocess requirement definition if version is not specified it adds latest available version.
    Then it returns package {requirement name, version, msg} or {name,available latest release version, msg}
    :param package:
    :param requirement: Definition of requirement
    :param allowed_operands:
    :param regex:
    :return:
    """
    p_name, operand, version_specifier = operand_parse(package, regex=regex)
    msg = ""
    if p_name is None:
        msg += f"ERROR: Requirement definition '{package}' is not valid."
    else:
        if operand not in allowed_operands:
            msg += f"ERROR: Operand '{operand}' is not allowed in requirement specifiers."
            p_name = None
        if version_specifier is None and operand is None:
            available_versions = get_available_package_versions(p_name)
            v = available_versions[0]
            if v == 'none':
                msg += f"ERROR: Package '{p_name}' has not any available version."
                p_name = None
            else:
                release_versions = [item for item in available_versions if not re.search('[a-zA-Z]', item)]
                # print(release_versions)
                if not release_versions:
                    version_specifier = available_versions[-1]
                    msg += f"WARNING : Version information not given for '{p_name}' choosing available latest " \
                           f"version : '{version_specifier}' "
                else:
                    version_specifier = release_versions[-1]
                    msg += f"WARNING : Version information not given for '{p_name}' choosing available latest " \
                           f"release version : '{version_specifier}' "
                    print_warning(msg)

    return p_name, version_specifier, msg


def operand_check(package_name):
    """
    A method that checks given package name contains version compare sign or not. If contains method returns operand
    :param package_name: Package name
    :return: operand string such ['==', '<=', '>=', '<', '>'] or None
    """
    operands = ['==', '<=', '>=', '<', '>']
    for op in operands:
        if op in package_name:
            return op
    return None


def preprocess_package(package, version_delim='=='):
    """
    A method that preprocesses given package. Then it returns package {name,version} or
    {name,available latest release version} if version not found in package name
    :param package: package name
    :param version_delim: version delimeter default is '=='
    :return:
    """
    n, op, v = operand_parse(package)
    msg = None
    if op is not None:
        n, v = package.split(op)
    else:
        available_versions = get_available_package_versions(package)
        v = available_versions[0]
        n = package
        if v == 'none':
            msg = f"ERROR: Package {package} not available."
        else:
            release_versions = [item for item in available_versions if not re.search('[a-zA-Z]', item)]
            v = release_versions[-1]
            msg = f"WARNING : Version information not given for '{n}' choosing available latest release version : '{v}'"

    return n.lower(), v, msg


def get_operand_from_condition(condition):
    """
    A method that extracts operand from compare condition such as '>=2.2.0'
    :param condition: String form of compare condition
    :return: operand(str), version(str)
    """
    operand = operand_check(condition)
    return operand, condition.replace(operand, "")


def control_condition(version_str, cond, delim=','):
    """
    A method that controls version condition according to expressions. If status is true condition is OK.
    :param version_str: version(str)
    :param cond: control conditions in string form merged with ',' such as '>=2.2.0,<2.2.7'
    :param delim:
    :return:
    """
    status = True
    if delim in cond:
        conds = cond.split(delim)
        for cnd in conds:
            expr, vcheck = get_operand_from_condition(cnd)
            status = status and ops[expr](version_str, vcheck)
    else:
        expr, vcheck = get_operand_from_condition(cond)
        status = status and (ops[expr](version_str, vcheck))
    return status


def query(package, db):
    """
    A method that checks package according to given vuln db
    :param package: package name
    :param db: vuln db
    :return: yields vuln versions of package from db
    """
    try:
        n, v, m = preprocess_package(package)
        for item in db[n]:
            for spec in item['specs']:
                if control_condition(v, spec):
                    yield item
        return None
    except KeyError:
        return None


def get_python_exec_path(python_path=None):
    """
    A method that returns python exec path according to os. If not it returns default python execution path
    :param python_path:
    :return:
    """
    if python_path is None:
        cmd = sys.executable
    else:
        if platform.system() == 'Windows':
            cmd = os.path.join(python_path, 'Scripts', 'python.exe')
        else:
            cmd = os.path.join(python_path, 'bin', 'python')
    if os.path.exists(cmd):
        return cmd
    else:
        if python_path == '.':
            python_path = os.getcwd()
        print_critical(f"Python not found in path {python_path}")

        exit()


def get_installed_pip_packages(env_dir=None):
    """
    A method that returns installed pip packages as set. To fasten existence control
    :param env_dir:
    :return:
    """
    cmd = get_python_exec_path(env_dir) + " -m pip freeze"

    package_str = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
    p_set = set(list(str(package_str).split('\n')))
    p_set.discard('')
    return p_set


def write_to_file(list_object, path=os.path.join(os.getcwd(), 'requirements.txt')):
    """
    A method that write list obj to file
    :param list_object: list obj
    :param path: output path
    :return:
    """
    with open(path, "w") as f:
        f.write("\n".join(str(item) for item in list_object))


def download_package(package_name, download_dir=os.path.join(os.getcwd(), "downloaded_packages")):
    """
    A method that download package to given directory
    :param package_name: name of package
    :param download_dir: download directory
    :return:
    """
    try:
        cmd = ' '.join([sys.executable, '-m pip download -d', download_dir, package_name])
        subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return {'Package_name': package_name, "Status": True, 'Message': None}
    except subprocess.CalledProcessError as error:
        print_critical(str(error))
        return {'Package_name': package_name, "Status": False, 'Message': error.output.decode('utf-8')}


def control_vulnerability(package_name, db_json):
    """
    A method that controls vulnerabilities according to given local vuln db
    :param package_name: name of package with version example "pipsec==1.0.0"
    :param db: vuln db
    :return:
    """
    res = list(query(package_name, db_json))
    rep = {}
    rep[package_name] = res
    if not res:
        return package_name, False, rep
    else:
        return package_name, True, rep


def get_available_package_versions(package_name):
    """
    A method that returns available versions of given package.
    :param package_name: Name of package. Example: tensorflow
    :return: list of versions. Ex: ['2.2.0rc1', '2.2.0rc2', '2.2.0rc3', ...]
    """
    cmd = 'pip install ' + package_name + "==="
    res = subprocess.run(cmd, shell=True, stderr=subprocess.PIPE).stderr.decode('utf-8')
    versions = res.split("(from versions: ")[1].split(')')[0].split(',')
    return [item.strip(' ') for item in versions]


def filter_by_sec(package_list, db_json):
    """
    A method that filters secure versions of given pip packages too help choosing secure version of given package
    :param package_list:
    :param db_json:
    :return:
    """
    secure = []
    for package in package_list:
        _, status, rep = control_vulnerability(package, db_json)
        if status:
            package = package.split('==')[0]
            versions = get_available_package_versions(package.split('==')[0])
            for v in versions:
                _, status, rep = control_vulnerability("==".join([package, v]), db_json)
                if not status:
                    secure.append(_)
                    continue
        else:
            secure.append(_)
    return secure


def mt_sec(package, db):
    """
    Multithreaded function for security check of packages
    :param package: package name
    :param db: vuln db
    :return:
    """
    all_rep = {}
    all_rep[package] = {}
    error_message = None
    try:
        _, status, rep = control_vulnerability(package, db)
        if status:
            all_rep = {**all_rep, **rep}
            package_name = package.split('==')[0]
            versions = get_available_package_versions(package_name)
            secure_packages = []
            for v in versions:
                _, status, rep = control_vulnerability("==".join([package_name, v]), db)
                if not status:
                    secure_packages.append(_)
                # else:
                #     all_rep = {**all_rep, **rep}

            if not secure_packages:
                error_message = f"!!! IMPORTANT !!! No alternative secure package versions found for package {package}."
                print_critical(error_message)
                return package, all_rep, error_message
            else:
                for pkg in secure_packages:
                    if version.parse(pkg.split("==")[1]) > version.parse(package.split('==')[1]):
                        error_message = f"Package: {package} is vulnerable replacing with package: {pkg}. Available " \
                                        f"secure versions are : {secure_packages} "
                        print_warning("WARNING : " + error_message)
                        return pkg, all_rep, error_message

                error_message = f'Package: {package} is vulnerable replacing with latest secure package: ' \
                                f'{secure_packages[-1]}. Available secure versions are : {secure_packages} '
                print_warning(error_message)
                return secure_packages[-1], all_rep, error_message
        else:
            return _, all_rep, error_message
    except Exception as e:
        error_message = str(e)
        return package, all_rep, error_message


def create_virtual_environment(environment_dir):
    """
    A method that creates python3 virtual environment to given directory
    :param environment_dir: directory of venv
    :return:
    """
    if not os.path.exists(environment_dir):
        cmd = ' '.join(['virtualenv -p python3', environment_dir])
        try:
            subprocess.run(cmd, shell=True, check=True)
        except Exception as e:
            raise e


def install_package(package_name, downloaded_package_dir, environment_dir=None):
    """
    A method that installs python package as online or offline from given downloaded package directory
    to given env or global site-packages
    :param package_name: Name of package
    :param downloaded_package_dir: Downloaded package directory for offline install
    :param environment_dir: Environment root directory if none it uses default python
    :return:
    """
    if downloaded_package_dir is None:
        cmd = ' '.join([get_python_exec_path(environment_dir), "-m pip install", package_name])
    else:
        cmd = ' '.join(
            [get_python_exec_path(environment_dir), "-m pip install --no-index --find-links", downloaded_package_dir,
             package_name])

    result = subprocess.run(cmd, shell=True, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise Exception(result.stderr.decode('utf-8'))


def report_and_install(args, package, package_set, report):
    """
    A method that control existence of package and installs it according to given args with report enrichment
    :param args: cl arguments
    :param package: package name
    :param package_set: set of installed packages
    :param report: report object
    :return: enriched report object
    """
    if package not in package_set:
        try:
            install_package(package, args.package_dir, args.environment_dir)
            report.add_success(package)
        except Exception as e:
            report.add_fail(package, str(e))
            pass
    else:
        report.add_exist(package)
    return report


def security_check_requirements(packages, db, report, auto_mode=True):
    """
    A method that check requirement security condition according to
    strictly(not allow) or auto mode(tries to replace with secure version)
    :param packages: List of packages
    :param db: Vuln db json
    :param report: report obj
    :param auto_mode: auto mode opt if true, it tries to replace with secure version
    :return: controlled list, filled report obj
    """
    result_packages = []
    if auto_mode:
        for package in packages:
            package_controlled, all_vuln, error_message = mt_sec(package, db)
            if error_message is not None:
                report.add_fail(package, error_message)
                report.extend_vulnerabilities(all_vuln)
            result_packages.append(package_controlled)
    else:
        for package in packages:
            package_controlled, status, rep = control_vulnerability(package, db)
            # If secure
            if not status:
                result_packages.append(package_controlled)
            # if vulnerable
            else:
                error_message = f"Package: {package_controlled} is vulnerable and not installed."
                report.add_fail(package_controlled, error_message)
                report.extend_vulnerabilities(rep)
                print_critical(error_message)
    return result_packages, report


def download_single_package(package_name, package_dir):
    """
    A method that downloads single package to given directory
    :param package_name: name of package
    :param package_dir: package download directory
    :return:
    """
    cmd = ' '.join([sys.executable, '-m pip --disable-pip-version-check download -d', package_dir, package_name])
    result = subprocess.run(cmd, shell=True, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise Exception(result.stderr.decode('utf-8'))


def uninstall_single_package(package_name, environment_dir=None):
    """
    A method that uninstalls single package from given python environment
    :param package_name: name of package
    :param environment_dir: environment dir to uninstall package
    :return:
    """
    cmd = ' '.join([get_python_exec_path(environment_dir), "-m pip uninstall", package_name, '-y'])
    result = subprocess.run(cmd, shell=True, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise Exception(result.stderr.decode('utf-8'))


def uninstall_from_requirements(requirements, environment_dir=None):
    """
    A method that uninstall packages defined in requirements file from given python environment
    :param requirements: requirements txt file
    :param environment_dir: environment dir to uninstall package
    :return:
    """
    for package in requirements:
        try:
            uninstall_single_package(package, environment_dir)
        except Exception as e:
            print_critical(e)
            pass