from .utils import *


class Requirements:
    def __init__(self, path=None, list_object=None):
        if path is not None:
            self.requirements = read_list_from_file(path)
        elif list_object is not None:
            self.requirements = list_object
        else:
            raise Exception("ERROR: Requirements not initialized properly...")

        self.requirement_regex = "(^[\w*\.*\-*]+)*\s*([<>=]+)*\s*(\d+.*)*\s*"
        self.allowed_operands = ["==", None]

    def parse_requirement(self, requirement):
        """
        A method that parse given requirement and returns (package_name, operand, version) tuple
        :param requirement: string requirement definition. e.g. tensorflow==2.2.1
        :return: (package_name, operand, version) tuple
        """
        return operand_parse(requirement, self.requirement_regex)

    def preprocess_requirement(self, requirement):
        """
        A method that preprocess requirement definition if version is not specified it adds latest available version.
        Then it returns package {requirement name, version, msg} or {name,available latest release version, msg}
        :param requirement: Definition of requirement
        :return:
        """
        # If requirement definition is commented just pass
        if requirement.strip().startswith('#'):
            return None, None, ''
        req_name, operand, version = self.parse_requirement(requirement)

    def check_requirement(self, requirement):
        return check_package(requirement, self.allowed_operands, regex=self.requirement_regex)

    def check_requirements(self):
        """
        A method that check requirements according to structural rules
        :return:
        """
        pname_set = set()
        valid_status = True
        error_messages = ""
        requirements = []
        for i, req in enumerate(self.requirements, 1):
            if req.strip().startswith('#'):
                continue
            pname, ver, msg = self.check_requirement(req)
            # print(pname,ver, msg)

            if pname is None:
                error_messages += f"Line: {i} - '{req}' | {msg}\n"
                valid_status = False
            else:
                if pname not in pname_set:
                    pname_set.add(pname)
                    requirements.append("==".join([pname, ver]))
                    if msg is not "":
                        error_messages += f"Line: {i} - '{req}' | {msg}\n"
                else:
                    error_messages += f"Line: {i} - '{req}' | ERROR: Duplicated requirement given : '{pname}'.\n"
                    valid_status = False
        self.requirements = requirements
        return requirements, valid_status, error_messages

    def save(self, path):
        try:
            write_list_to_file(self.requirements, path)
        except Exception as e:
            raise e

    def load(self, path):
        try:
            self.requirements = read_list_from_file(path)
        except Exception as e:
            raise e
