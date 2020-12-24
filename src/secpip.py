from .requirements import Requirements
from .utils import *
from .report import Report
import json
import sys
import argparse
import os
from .headers import *
import requests
from src import __version__

class Secpip(object):
    def __init__(self):
        allowed_commands = {'install', 'dump', 'uninstall', 'migrate', 'sync'}
        print(intro)
        parser = argparse.ArgumentParser(description="Secure pip package manager...",
                                         formatter_class=argparse.RawDescriptionHelpFormatter,
                                         usage="""secpip <command> [<args>]
Commands:
  install\t\tInstall pip packages by using secpip abilities (secure, report, auto_mode)
  dump\t\t\tPackage/Download pip packages by using secpip abilities (secure, report, auto_mode)
  uninstall\t\tUninstall pip packages from venv as single or batch from requirements
  migrate\t\tMigrate virtual environment to another one securely
  sync\t\t\tSynchronize Database from web
General Options:
  --secure\t\tSecure option to check known vulnerabilities. If package is not secure operation not allowed to package
  --auto\t\tUse with secure option. It replace vulnerable package with next secure version, If no secure package exists it create warning and install insecure one.      
""",
                                         epilog="--Be aware of your weakness before darkness--")

        parser.add_argument('command', help='{install, dump, uninstall}')
        parser.add_argument('-V', '--version', action='version', version='%(prog)s ' + __version__)

        if not sys.argv[1:2]:
            parser.print_help()
            return
        else:
            args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command) or args.command not in allowed_commands:
            parser.print_help()
            print_critical(f"Unrecognized secpip command '{args.command}'")
            return

        self.db_path = os.path.join(os.path.split(__file__)[0], '../db/vulndb_full.json')
        self.db_url = "https://raw.githubusercontent.com/myasinsaglam/secpip/master/db/vulndb_full.json"
        # Loading vuln db from file
        with open(os.path.join(os.path.split(__file__)[0], '../db/vulndb_full.json'), 'r') as fp:
            self.db = json.load(fp)
        # using dispatch pattern to invoke method with same name
        getattr(self, args.command)()

    def sync(self):
        try:
            r = requests.get(self.db_url).json()
            # Loading vuln db from file
            with open(self.db_path, 'w') as fpw:
                json.dump(r, fpw)
            print_success("Sync completed successfully...")
        except Exception as e:
            print_critical(e)
            raise e

    def install_single_package(self, package_name, args):
        """
        A method that executes the logic of SECPIP's single packet installation
        :param package_name: name of packages
        :param args: Command line arguments
        :return: None
        """
        if args.FLAG_SEC and args.FLAG_AUTO:
            package, all_vuln, error_message = mt_sec(package_name, self.db)
            install_package(package, args.package_dir, args.environment_dir)
        elif args.FLAG_SEC and not args.FLAG_AUTO:
            package, status, rep = control_vulnerability(package_name, self.db)
            if not status:
                install_package(package, args.package_dir, args.environment_dir)
            else:
                print_critical(f"Package: {package} is vulnerable and not installed.")
        elif not args.FLAG_SEC:
            install_package(package_name, args.package_dir, args.environment_dir)

    def install_from_requirements(self, args):
        """

        :param args:
        :return:
        """
        if not os.path.exists(args.requirements_dir):
            raise Exception(f"Requirement file {args.requirements_dir} not found.")
        else:
            reqs_obj = Requirements(args.requirements_dir)

        if args.package_dir is not None and not os.path.exists(args.package_dir):
            raise Exception(f"Offline package directory not found in {args.package_dir}")

        report = Report('Install', args.environment_dir, args.package_dir, args.report_dir)
        package_set = get_installed_pip_packages(args.environment_dir)

        packages, req_validity, msg = reqs_obj.check_requirements()

        if not req_validity:
            raise Exception(f"Requirement file {args.requirements_dir} need to fix some issue(s) before operation "
                            f"start\n{msg}")

        if args.FLAG_SEC:
            packages, report = security_check_requirements(packages, self.db, report, args.FLAG_AUTO)
        for package in packages:
            report = report_and_install(args, package, package_set, report)

        print("REPORT: ")
        report.print_report()
        if args.report_dir is not None:
            report.save(args.report_dir)

    def install(self):
        """
        Install mode function that contains secure, report, multiple and one package install
        :return:
        """

        parser = argparse.ArgumentParser(description='Install pip packages as online or offline with security check')
        parser.add_argument('--secure', action='store_true', dest='FLAG_SEC', help='A flag for security check option')
        parser.add_argument('--auto', action='store_true', dest='FLAG_AUTO',
                            help='A flag for auto correct versions by replacing secure one')
        parser.add_argument('--report', required=False, dest='report_dir', help='Report Extraction Option')

        # Environment directory
        parser.add_argument('-v', '--venv_dir', required=False, dest='environment_dir',
                            help='Python environment path to install modules')

        parser.add_argument('-p', '--package_dir', required=False, dest='package_dir',
                            help='Downloaded package directory for offline install')

        parser.add_argument('-r', '--requirements_file', required=False, dest='requirements_dir',
                            default=os.path.join(os.getcwd(), 'requirements.txt'),
                            help='Requirements txt i/o file path, default is {current_path}/requirements.txt')
        try:
            arguments, package_name = (sys.argv[2:], None) if sys.argv[2].startswith('-') or sys.argv[2].startswith(
                '--') else (sys.argv[3:], sys.argv[2])
        except IndexError:
            parser.print_help()
            return

        args = parser.parse_args(arguments)
        if args.environment_dir is not None:
            create_virtual_environment(args.environment_dir)
        # Single package install part
        if package_name is not None:
            try:
                self.install_single_package(package_name, args)
            except Exception as e:
                print_critical(e)
                pass
        # Install from requirement file part
        else:
            try:
                self.install_from_requirements(args)
            except Exception as e:
                print_critical(e)
                pass

    def dump_single_package(self, package_name, args):
        if args.package_dir is None:
            raise Exception(f"Package directory needed to run this command\n")
        if args.FLAG_SEC and args.FLAG_AUTO:
            package, all_vuln, error_message = mt_sec(package_name, self.db)
            download_single_package(package, args.package_dir)
        elif args.FLAG_SEC and not args.FLAG_AUTO:
            package, status, rep = control_vulnerability(package_name, self.db)
            if not status:
                download_single_package(package, args.package_dir)
            else:
                print(f"Package: {package} is vulnerable and not downloaded.")
        elif not args.FLAG_SEC:
            download_single_package(package_name, args.package_dir)

    def dump_from_source(self, args):
        """

        :param args:
        :return:
        """
        report = Report('Dump', args.environment_dir, args.package_dir, args.report_dir)
        if args.environment_dir is not None:
            package_set = get_installed_pip_packages(args.environment_dir)
            reqs = Requirements(list_object=list(package_set))
            if args.package_dir is not None:
                if args.FLAG_SEC:
                    reqs.requirements, report = security_check_requirements(reqs.requirements, self.db, report,
                                                                            args.FLAG_AUTO)
                for package in reqs.requirements:
                    try:
                        download_single_package(package, args.package_dir)
                        report.add_success(package)
                    except Exception as e:
                        report.add_fail(package, str(e))

                reqs = Requirements(list_object=report.get_success())
                print("REPORT: ")
                report.print_report()
                if args.report_dir is not None:
                    report.save(args.report_dir)

            reqs.save(args.requirements_dir)
        else:
            if args.package_dir is not None:
                try:
                    reqs = Requirements(args.requirements_dir)
                except:
                    package_set = get_installed_pip_packages(args.environment_dir)
                    reqs = Requirements(list_object=list(package_set))
                # reqs = Requirements(args.requirements_dir)
                packages, req_validity, msg = reqs.check_requirements()
                if not req_validity:
                    if not args.FLAG_AUTO:
                        raise Exception(
                            f"Requirement file {args.requirements_dir} need to fix some issue(s) before operation "
                            f"start\n{msg}")
                if args.FLAG_SEC:
                    reqs.requirements, report = security_check_requirements(reqs.requirements, self.db, report,
                                                                            args.FLAG_AUTO)
                for package in reqs.requirements:
                    try:
                        download_single_package(package, args.package_dir)
                        report.add_success(package)
                    except Exception as e:
                        report.add_fail(package, str(e))

                reqs = Requirements(list_object=report.get_success())
                reqs.save(args.requirements_dir)
                print("REPORT: ")
                report.print_report()
                if args.report_dir is not None:
                    report.save(args.report_dir)

    def dump(self):
        """
        Package mode function that contains secure, report, multiple and one package download
        :return:
        """

        desc = f'''Dump pip packages:
            - from package name to to directory as setup file
            - from requirements to directory as setup files
            - from venv to directory as setup files
            - from venv to requirements as metadata'''

        parser = argparse.ArgumentParser(description=desc, formatter_class=argparse.RawDescriptionHelpFormatter)
        parser.add_argument('--secure', action='store_true', dest='FLAG_SEC', help='A flag for security check option')
        parser.add_argument('--auto', action='store_true', dest='FLAG_AUTO', help='A flag for auto correct versions')
        parser.add_argument('--report', required=False, dest='report_dir', help='Report Extraction Option')

        # Environment directory
        parser.add_argument('-v', '--venv_dir', required=False, dest='environment_dir',
                            help='Python environment path to extract installed modules')

        parser.add_argument('-p', '--package_dir', required=False, dest='package_dir',
                            help='Downloaded package directory for offline install')

        # Requirements file that will be generated after packaging
        parser.add_argument('-r', '--requirements_file', required=False, dest='requirements_dir',
                            default=os.path.join(os.getcwd(), 'requirements.txt'),
                            help='Requirements txt i/o file path, default is {current_path}/requirements.txt')
        try:
            arguments, package_name = (sys.argv[2:], None) if sys.argv[2].startswith('-') or sys.argv[2].startswith(
                '--') else (sys.argv[3:], sys.argv[2])
        except IndexError:
            parser.print_help()
            return

        args = parser.parse_args(arguments)

        # Single package dump part
        if package_name is not None:
            try:
                self.dump_single_package(package_name, args)
            except Exception as e:
                print_critical(e)
                pass
        # Install from requirement file part
        else:
            try:
                self.dump_from_source(args)
            except Exception as e:
                print_critical(e)
                pass

    def uninstall(self):
        parser = argparse.ArgumentParser(description='Uninstall pip packages as batch by using requirement file')
        # Environment directory
        parser.add_argument('-v', '--venv_dir', required=False, dest='environment_dir',
                            help='Python environment path that will be uninstall modules from')

        parser.add_argument('-r', '--requirements_file', required=False, dest='requirements_dir',
                            default=os.path.join(os.getcwd(), 'requirements.txt'),
                            help='Requirements txt i/o file path, default is {current_path}/requirements.txt')
        try:
            arguments, package_name = (sys.argv[2:], None) if sys.argv[2].startswith('-') or sys.argv[2].startswith(
                '--') else (sys.argv[3:], sys.argv[2])
        except IndexError:
            parser.print_help()
            return

        args = parser.parse_args(arguments)
        if package_name is not None:
            try:
                uninstall_single_package(package_name, args.environment_dir)
            except Exception as e:
                print_critical(e)
                pass
        # Install from requirement file part
        else:
            try:
                reqs_obj = Requirements(args.requirements_dir)
                uninstall_from_requirements(reqs_obj.requirements, args.environment_dir)
            except Exception as e:
                print_critical(e)
                pass

    def migrate_env(self, args):
        """
        A method that migrate venv to another one
        :param args:
        :return:
        """
        report = Report('Migrate', report_path=args.report_dir,
                        SourceEnvironment=args.src_venv,
                        DestinationEnvironment=args.dst_venv)

        packages = list(get_installed_pip_packages(args.src_venv))
        package_set = get_installed_pip_packages(args.dst_venv)

        if args.FLAG_SEC:
            packages, report = security_check_requirements(packages, self.db, report, args.FLAG_AUTO)
        for package in packages:
            if package not in package_set:
                try:
                    install_package(package, None, args.dst_venv)
                    report.add_success(package)
                except Exception as e:
                    report.add_fail(package, str(e))
                    pass
            else:
                report.add_exist(package)
        print("REPORT: ")
        report.print_report()
        if args.report_dir is not None:
            report.save(args.report_dir)

    def migrate(self):
        parser = argparse.ArgumentParser(description='Migrate virtual environment to another virtual environment')
        parser.add_argument('--secure', action='store_true', dest='FLAG_SEC', help='A flag for security check option')
        parser.add_argument('--auto', action='store_true', dest='FLAG_AUTO', help='A flag for auto correct versions')
        parser.add_argument('--report', required=False, dest='report_dir', help='Report Extraction Option')

        # Environment directory
        parser.add_argument('-s', '--src', required=True, dest='src_venv',
                            help='Source Python environment path to migrate modules')

        parser.add_argument('-d', '--dst', required=True, dest='dst_venv',
                            help='Destination Python environment path to migrate modules')

        try:
            arguments, package_name = (sys.argv[2:], None) if sys.argv[2].startswith('-') or sys.argv[2].startswith(
                '--') else (sys.argv[3:], sys.argv[2])
        except IndexError:
            parser.print_help()
            return

        args = parser.parse_args(arguments)
        if args.dst_venv is not None:
            create_virtual_environment(args.dst_venv)
        try:
            self.migrate_env(args)
        except Exception as e:
            print_critical(e)
            pass


def main():
    Secpip()
