from django.core.management.base import BaseCommand, CommandError

class BasicCommand(BaseCommand):
    def _write(self, output):
        self.stdout.write(str(output))

    def _error(self, output):
        self.stderr.write(str(output))

    def _heading(self, output):
        self.stdout.write(self.style.MIGRATE_HEADING(output))

    def _label(self, output):
        self.stdout.write(self.style.MIGRATE_LABEL(output))

    def _label_inline(self, output):
        return self.style.MIGRATE_LABEL(output)

    def _notice(self, output):
        self.stdout.write(self.style.NOTICE(output))

    def _success(self, output):
        self.stdout.write(self.style.SUCCESS(output))

    def _yesno(self, question, default="yes"):
        valid = {"yes": True, "y": True, "ye": True,
                 "no": False, "n": False}
        if default is None:
            prompt = " [y/n] "
        elif default == "yes":
            prompt = " [Y/n] "
        elif default == "no":
            prompt = " [y/N] "
        else:
            raise ValueError("invalid default answer: '%s'" % default)

        while True:
            self._write(question + prompt)
            choice = input().lower()
            if default is not None and choice == '':
                return valid[default]
            elif choice in valid:
                return valid[choice]
            else:
                self._write("Please respond with 'yes' or 'no' "
                                 "(or 'y' or 'n').\n")