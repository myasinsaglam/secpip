import json
import os


class Report:

    def __init__(self, optype=None, env_dir=None, package_dir=None, report_path=None, **kwargs):
        self.key_success = 'Success'
        self.key_fail = 'Failed'
        self.key_exist = 'Existed'
        self.key_vulnerable = 'VulnerabilityDetails'
        self.key_optype = 'OperationType'
        self.key_environment = 'Environment'
        self.key_package_dir = 'OfflinePackageDirectory'
        self.key_report_path = 'ReportPath'
        if not kwargs:
            self.report = {self.key_optype: optype, self.key_environment: env_dir, self.key_package_dir: package_dir,
                           self.key_report_path: report_path, self.key_success: [], self.key_fail: {},
                           self.key_exist: [],
                           self.key_vulnerable: {}}
        else:
            self.report = {self.key_optype: optype, self.key_environment: env_dir, self.key_package_dir: package_dir,
                           **kwargs,
                           self.key_report_path: report_path,
                           self.key_success: [],
                           self.key_fail: {},
                           self.key_exist: [],
                           self.key_vulnerable: {}}

    def add_success(self, package_name):
        """
        A method that add operation succedeed package name to the report
        :param package_name: name of package
        :return:
        """
        if package_name not in set(self.report[self.key_success]):
            self.report[self.key_success].append(package_name)

    def get_success(self):
        """
        A method that retrive packages that operation done succesfully
        :return:
        """
        return self.report[self.key_success]

    def add_fail(self, package_name, message=None):
        """
        A method that add operation failed package name to the report
        :param package_name: name of package
        :param message: fail message
        :return:
        """
        self.report[self.key_fail][package_name] = message

    def add_exist(self, package_name):
        """
        A method that add existed package name to the report
        :param package_name: name of package
        :return:
        """
        if package_name not in set(self.report[self.key_exist]):
            self.report[self.key_exist].append(package_name)

    def add_vulnerability(self, package_name, vuln_details=None):
        """
        A method that add vulnerability info with package name to the report
        :param package_name: name of package
        :param vuln_details: vulnerability details
        :return:
        """
        self.report[self.key_vulnerable][package_name] = vuln_details

    def extend_vulnerabilities(self, vuln_json):
        """
        A method that extend vuln info in report with given json.
        :param vuln_json:
        :return:
        """
        self.report[self.key_vulnerable] = {**self.report[self.key_vulnerable], **vuln_json}

    def set_operation(self, op_name):
        """
        A method that sets operation name for report
        :param op_name: name of operation
        :return:
        """
        self.report[self.key_optype] = op_name

    def set_environment(self, env_name):
        """
        A method that sets python environment name for report
        :param env_name:
        :return:
        """
        self.report[self.key_environment] = env_name

    def set_package_dir(self, package_dir):
        """
        A method that sets package directory name for report
        :param package_dir:
        :return:
        """
        self.report[self.key_package_dir] = package_dir

    def set_report_path(self, report_path):
        """
        A method that sets report path name for report
        :param report_path:
        :return:
        """
        self.report[self.key_report_path] = report_path

    def save(self, path, filter_none=True):
        """
        A method that save report to file
        :param path: report file path
        :param filter_none: filters none valued keys in report
        :return:
        """
        if filter_none:
            self.report = {
                k: v
                for k, v in self.report.items()
                if v is not None
            }
        if path is None:
            path = os.path.join(os.getcwd(), 'report.json')
        with open(path, 'w') as fpw:
            json.dump(self.report, fpw)

    def print_report(self, filter_none=True):
        """
        A method that prints report.
        :param filter_none: filters none valued keys in report
        :return:
        """
        if filter_none:
            self.report = {
                k: v
                for k, v in self.report.items()
                if v is not None
            }
        json_formatted_str = json.dumps(self.report, indent=2)
        print(json_formatted_str)
